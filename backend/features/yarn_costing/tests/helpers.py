"""Shared test data: the real numbers of S4-2017 and S1-1310 (copied from the two Excel workbooks)."""

from datetime import date
from decimal import Decimal

from backend.features.yarn_costing.dto.common_dto import ActorDTO, YarnComponentDTO
from backend.features.yarn_costing.dto.loss_dto import CreatePrimaryLossGroupRequest
from backend.features.yarn_costing.dto.master_dto import (
    ApplyRateVersionRequest,
    PackagingRowDTO,
    RateLineRowDTO,
    SavePackagingTypesRequest,
)
from backend.features.yarn_costing.dto.request_dto import CreateYarnRequestRequest
from backend.features.yarn_costing.dto.user_dto import GroupMemberRowDTO, SaveUserGroupRequest
from backend.features.yarn_costing.models.enums import FactoryCode, Technology
from backend.features.yarn_costing.repositories.stage_repository import StageRepository
from backend.features.yarn_costing.services.apply_rate_version_service import ApplyRateVersionService
from backend.features.yarn_costing.services.create_primary_loss_group_service import CreatePrimaryLossGroupService
from backend.features.yarn_costing.services.create_yarn_request_service import CreateYarnRequestService
from backend.features.yarn_costing.services.save_packaging_types_service import SavePackagingTypesService
from backend.features.yarn_costing.services.save_user_group_service import SaveUserGroupService

D = Decimal

SO = ActorDTO(group_code="SO", access_code="SO0000", person_name="Phòng SO")
TODAY = date.today()

MD_S4 = ("430.908759098888", "142.65553199032365", "60.092337370786986", "20.86446552646605", "47.57495512833889")
S4_RATES = {
    "C1": ("113.55205632639183", "421.8443936690036", "1533.6355886940446", "297.5751363895607", "172.02078159931187"),
    "C3": ("163.71195368991093", "262.659290682775", "1330.150700664721", "306.6993672916976", "149.96867519737955"),
    "CM": ("356.2972036152069", "470.30616695583035", "224.89732068872294", "39.01967861871709", "79.26628819174616"),
    "MD1": MD_S4,
    "MD2": MD_S4,
    "MD3": MD_S4,
    "V": ("762.7142138180886", "782.2345338130609", "2798.345816731206", "139.07015762115995", "325.808140450283"),
    "Type 3": ("1151.959417735043", "238.64599581875655", "0", "2785.4556288636845", "303.5439476765351"),
}
S4_PACKAGING = ("Type 3", D("0.2194564694564695"))
S4_LOSSES = {
    "V": D("0.0315"),
    "MD3": D("0.002"),
    "MD2": D("0.002"),
    "MD1": D("0.0006"),
    "CM": D("0.145"),
    "SBD": D("0.0034999999999999996"),
    "C3": D("0.034"),
    "C1": D("0.07500000000000001"),
}
S4_NAME = "CORE 40/1 (COTTON/ FDY 30D/24F/1) (70/30) MVS"
S4_NSM = {"CM": D(50), "MD1": D(100), "MD2": D(90), "MD3": D(83), "V": D(25)}
# 4.12.1: Cotton 70% on C1, the material of cell 'Other - C3.3' 30% on C3 (pass 1)
S4_COMPONENTS = [
    YarnComponentDTO(material_label="Cotton", ratio=D("0.7"), carding_stage="C1", nsm_carding=D(45)),
    YarnComponentDTO(material_label="Other - C3.3", ratio=D("0.3"), carding_stage="C3", nsm_carding=D(45)),
]
# The same yarn in the layout of the old Excel file (5.2): blend cells + NSM columns C1 / C3.3
S4_FILE_NSM = {"C1": D(45), "C3.3": D(45), **S4_NSM}
S4_FILE_BLEND = {"Cotton": D("0.7"), "Other - C3.3": D("0.3")}

MD_S1 = ("224.5965604096536", "83.37218971058164", "122.16540764712867", "42.06152412098955", "47.41285671607104")
S1_RATES = {
    "C1": ("205.2246618955186", "195.7690174134529", "336.60608187717935", "374.95359413981595", "111.71074799774695"),
    "PD2": MD_S1,
    "MD1": MD_S1,
    "MD2": MD_S1,
    "MD3": ("404.2733598871511", "161.8002761068613", "153.23656326877074", "55.16249991649634", "77.7642924853728"),
    "V": ("686.3362580655952", "1001.1461116929087", "1031.7999393375626", "505.98936721405977", "323.84739997569636"),
    "Type 1": ("875.4194309963544", "1315.0320273914715", "0", "4423.839055060779", "664.1365442785968"),
}
S1_PACKAGING = ("Type 1", D("0.24439405391786342"))
S1_LOSSES = {"V": D("0.032"), "MD3": D("0.0052"), "MD2": D("0.0052"), "MD1": D("0.0052"), "C1": D("0.0168")}
S1_NAME = "TC 20/1 (60/40) MVS"
S1_NSM = {
    "PD2": D("76.03"),
    "MD1": D("76.03"),
    "MD2": D("76.03"),
    "MD3": D("65.66"),
    "V": D("39.120999999999995"),
}
S1_COMPONENTS = [
    YarnComponentDTO(material_label="PE", ratio=D("0.6"), carding_stage="C1", nsm_carding=D(18)),
    YarnComponentDTO(material_label="Cotton", ratio=D("0.4"), carding_stage=""),
]


def rate_rows(factory: FactoryCode, rates: dict, packaging_code: str) -> list[RateLineRowDTO]:
    """Every stage of the factory gets a rate (the known ones from the workbook, MD values for the others)."""
    default = rates["MD1"]
    codes = [s.stage_code for s in StageRepository().for_factory(factory.value) if not s.is_packaging] + [
        packaging_code
    ]
    rows = []
    for code in codes:
        values = rates.get(code, default)
        rows.append(
            RateLineRowDTO(
                rate_code=code,
                labor=D(values[0]),
                depreciation=D(values[1]),
                electricity=D(values[2]),
                materials=D(values[3]),
                overhead=D(values[4]),
            )
        )
    return rows


def setup_factory(factory: FactoryCode = FactoryCode.S4, with_loss_group: bool = True) -> None:
    """Packaging + rate version (+ the loss group of the reference yarn) through the real use cases."""
    rates, packaging, losses, name = (
        (S4_RATES, S4_PACKAGING, S4_LOSSES, S4_NAME)
        if factory == FactoryCode.S4
        else (S1_RATES, S1_PACKAGING, S1_LOSSES, S1_NAME)
    )
    SavePackagingTypesService().handle(
        SavePackagingTypesRequest(
            actor=SO,
            factory_code=factory,
            rows=[PackagingRowDTO(code=packaging[0], name=packaging[0], minutes_per_kg=packaging[1])],
        )
    )
    ApplyRateVersionService().handle(
        ApplyRateVersionRequest(
            actor=SO,
            factory_code=factory,
            rows=rate_rows(factory, rates, packaging[0]),
            effective_date=TODAY,
            reason="Định mức 2026",
        )
    )
    if with_loss_group:
        label = name.replace(name.split()[1] + " ", "", 1) if factory == FactoryCode.S4 else "TC (60/40) MVS"
        CreatePrimaryLossGroupService().handle(
            CreatePrimaryLossGroupRequest(
                actor=SO, factory_code=factory, yarn_group_label=label, technology=Technology.MVS, losses=losses
            )
        )


def add_member(group_code: str, access_code: str, name: str) -> ActorDTO:
    names = {"SALES": "Sales", "XS1": "Xưởng Sợi 1", "XS4": "Xưởng Sợi 4", "KT": "Kế toán"}
    SaveUserGroupService().handle(
        SaveUserGroupRequest(
            actor=SO, group_code=group_code, name=names[group_code], members=[GroupMemberRowDTO(name=name)]
        )
    )
    return ActorDTO(group_code=group_code, access_code=access_code, person_name=name)


def create_request(name: str, factory: FactoryCode = FactoryCode.S4, packaging: str = "Type 3") -> str:
    return (
        CreateYarnRequestService()
        .handle(CreateYarnRequestRequest(actor=SO, factory_code=factory, yarn_name=name, packaging_code=packaging))
        .yarn.yarn_code
    )
