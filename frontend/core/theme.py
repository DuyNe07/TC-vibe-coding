"""Global look & feel (CSS). Applied once per run by AppShell. Features must not inject global CSS."""

import streamlit as st

PRIMARY = "#0F62FE"

_CSS = f"""
<style>
  .block-container {{ padding-top: 1.6rem; padding-bottom: 1rem; max-width: 1400px; }}

  /* ---- page header ---- */
  .tc-page-header {{ padding: 0 0 .9rem 0; margin-bottom: 1.1rem; border-bottom: 1px solid rgba(128,128,128,.22); }}
  .tc-breadcrumb {{ font-size: .8rem; opacity: .62; margin-bottom: .35rem; letter-spacing: .01em; }}
  .tc-breadcrumb span.sep {{ margin: 0 .4rem; opacity: .6; }}
  .tc-title {{ font-size: 1.85rem; font-weight: 700; line-height: 1.25; display: flex; gap: .6rem; align-items: center; }}
  .tc-desc {{ margin: .35rem 0 0 0; opacity: .75; font-size: .98rem; }}

  /* ---- hero (home) ---- */
  .tc-hero {{ padding: 1.6rem 1.8rem; border-radius: 14px; margin-bottom: 1.4rem;
              background: linear-gradient(120deg, {PRIMARY} 0%, #6929C4 100%); color: #fff; }}
  .tc-hero h1 {{ color: #fff; font-size: 2rem; margin: 0 0 .3rem 0; padding: 0; }}
  .tc-hero p {{ margin: 0; opacity: .9; font-size: 1.02rem; }}
  .tc-hero .tc-hero-meta {{ margin-top: .9rem; font-size: .82rem; opacity: .85; }}

  /* ---- panel / cards ---- */
  div[class*="st-key-tc-card-"] {{ transition: transform .12s ease, box-shadow .12s ease; }}
  div[class*="st-key-tc-card-"]:hover {{ transform: translateY(-2px); box-shadow: 0 6px 18px rgba(15,98,254,.14); }}
  .tc-card-title {{ font-size: 1.08rem; font-weight: 650; margin-bottom: .25rem; }}
  .tc-card-desc {{ font-size: .9rem; opacity: .78; min-height: 3.6em; }}
  .tc-card-meta {{ font-size: .75rem; opacity: .6; margin-top: .35rem; }}
  .tc-panel-title {{ font-weight: 650; font-size: 1.02rem; }}
  .tc-empty {{ text-align: center; padding: 2rem 1rem; opacity: .7; }}
  .tc-empty .tc-empty-icon {{ font-size: 2.2rem; }}

  /* ---- sidebar menu ---- */
  .tc-brand {{ display: flex; align-items: center; gap: .7rem; padding: .2rem 0 .9rem 0; }}
  .tc-brand-logo {{ width: 34px; height: 34px; border-radius: 9px; display: grid; place-items: center;
                    background: {PRIMARY}; color: #fff; font-weight: 800; font-size: .9rem; }}
  .tc-brand-img {{ height: 52px; width: auto; max-width: 45%; object-fit: contain; flex-shrink: 0; }}
  .tc-brand-name {{ font-weight: 700; font-size: 1.02rem; line-height: 1.1; }}
  .tc-brand-sub {{ font-size: .72rem; opacity: .6; }}
  .tc-nav-group {{ font-size: .7rem; font-weight: 700; text-transform: uppercase; letter-spacing: .06em;
                   opacity: .55; margin: .9rem 0 .15rem .2rem; }}

  /* ---- footer ---- */
  .tc-footer {{ margin-top: 3rem; padding: 1rem 0 .4rem 0; border-top: 1px solid rgba(128,128,128,.22);
                font-size: .78rem; opacity: .6; display: flex; justify-content: space-between; flex-wrap: wrap; gap: .5rem; }}
</style>
"""


def apply_theme() -> None:
    st.html(_CSS)
