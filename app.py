import time

import pandas as pd
import streamlit as st

st.set_page_config(page_title="Ocenenie firmy", layout="centered")


# JEDNODUCHÁ "PRIHLASOVACIA" VRSTVA
# Poznámka: pre účely case study stačí demo login. Nie je to produkčná aplikácia, takže bezpečnosť nie je prioritou.

DEMO_USERNAME = "demo"
DEMO_PASSWORD = "demo123"

# Odvetvové násobky EBITDA (ilustračné, zjednodušené hodnoty)
# V reálnej appke by tieto čísla pochádzali z databázy trhových dát

INDUSTRY_MULTIPLES = {
    "Obchod / maloobchod": 3.5,
    "Výroba": 4.5,
    "IT / softvér": 6.0,
    "Stavebníctvo": 3.0,
    "Gastro / hotelierstvo": 3.0,
    "Služby (všeobecné)": 4.0,
}

# Miera kapitalizácie podľa odvetvia (čím rizikovejšie/menej stabilné, tým vyššia)
CAP_RATES = {
    "Obchod / maloobchod": 0.20,
    "Výroba": 0.18,
    "IT / softvér": 0.15,
    "Stavebníctvo": 0.22,
    "Gastro / hotelierstvo": 0.25,
    "Služby (všeobecné)": 0.18,
}

METHOD_OPTIONS = {
    "Kombinácia oboch metód (odporúčané)": "combined",
    "Iba násobok EBITDA": "ebitda",
    "Iba kapitalizácia zisku": "income",
}


def login_screen():
    st.title("Prihlásenie")
    st.caption("Demo prístup pre účely case study.")

    with st.form("login_form"):
        username = st.text_input("Používateľské meno")
        password = st.text_input("Heslo", type="password")
        submitted = st.form_submit_button("Prihlásiť sa", type="primary")

        if submitted:
            if username == DEMO_USERNAME and password == DEMO_PASSWORD:
                st.session_state["logged_in"] = True
                st.rerun()
            else:
                st.error("Nesprávne meno alebo heslo.")


def validate_inputs(revenue, ebitda, net_profit, years_in_business):
    """
    Overí vstupné hodnoty. Vracia dvojicu (errors, warnings):
    - errors  = zabránia výpočtu (nulové/záporné kľúčové hodnoty)
    - warnings = výpočet prebehne, ale upozornia na nezvyčajné hodnoty
    """
    errors = []
    warnings = []

    if revenue < 0:
        errors.append("Ročné tržby nemôžu byť záporné číslo.")
    if ebitda < 0:
        errors.append("EBITDA nemôže byť záporné číslo.")
    if net_profit < 0:
        errors.append("Čistý zisk nemôže byť záporné číslo.")
    if years_in_business < 0:
        errors.append("Počet rokov podnikania nemôže byť záporné číslo.")

    if revenue == 0:
        errors.append("Zadajte ročné tržby väčšie ako 0.")
    if ebitda == 0 and net_profit == 0:
        errors.append(
            "Zadajte aspoň jednu z hodnôt EBITDA alebo čistý zisk väčšiu ako 0 "
            "- z nej nástroj počíta ocenenie."
        )

    if revenue > 0 and ebitda > revenue:
        warnings.append(
            "EBITDA je vyššia ako ročné tržby - skontrolujte, či sú hodnoty "
            "zadané správne."
        )
    if revenue > 0 and net_profit > revenue:
        warnings.append(
            "Čistý zisk je vyšší ako ročné tržby - skontrolujte, či sú "
            "hodnoty zadané správne."
        )
    if revenue > 50_000_000:
        warnings.append(
            "Zadané tržby sú nezvyčajne vysoké pre malú/strednú firmu - "
            "over si prosím, že ide skutočne o eurá, nie napr. o tisíce eur."
        )

    return errors, warnings


def calculate_valuation(revenue, ebitda, net_profit, industry, years_in_business, method):
    """
    Vracia rozpätie hodnoty firmy na základe zvolenej metódy (alebo kombinácie):
    1. Násobok EBITDA (Market approach - zjednodušený)
    2. Kapitalizácia čistého zisku (Income approach - zjednodušený)

    Ročné tržby vstupujú do výpočtu cez EBITDA maržu (ebitda / tržby), ktorá
    upravuje použitý násobok - firma s vyššou maržou je efektívnejšia a
    zvyčajne dosahuje vyššie ocenenie.

    Toto NIE JE presné profesionálne ocenenie - ide o indikatívny odhad
    pre malých podnikateľov, ktorí nemusia mať prístup k detailným M&A dátam.
    """
    base_multiple = INDUSTRY_MULTIPLES[industry]

    #Úprava podľa počtu rokov podnikania
    if years_in_business >= 10:
        years_adjustment = 1.10
        years_note = "10 a viac rokov podnikania zvyšuje násobok (nižšie vnímané riziko)."
    elif years_in_business >= 5:
        years_adjustment = 1.00
        years_note = "5-9 rokov podnikania má neutrálny vplyv na násobok."
    else:
        years_adjustment = 0.85
        years_note = "menej ako 5 rokov podnikania znižuje násobok (vyššie vnímané riziko)."

    # Úprava podľa EBITDA marže (tu do výpočtu vstupujú tržby
    margin = (ebitda / revenue) if revenue > 0 else 0
    if margin >= 0.20:
        margin_adjustment = 1.10
        margin_note = f"EBITDA marža {margin * 100:.1f} % je vysoká a zvyšuje násobok."
    elif margin >= 0.10:
        margin_adjustment = 1.00
        margin_note = f"EBITDA marža {margin * 100:.1f} % je priemerná, neutrálny vplyv."
    else:
        margin_adjustment = 0.90
        margin_note = f"EBITDA marža {margin * 100:.1f} % je nízka a znižuje násobok."

    adjusted_multiple = base_multiple * years_adjustment * margin_adjustment
    ebitda_valuation = ebitda * adjusted_multiple if ebitda > 0 else 0

    cap_rate = CAP_RATES[industry]
    income_valuation = net_profit / cap_rate if net_profit > 0 and cap_rate > 0 else 0

    if method == "ebitda":
        base_value = ebitda_valuation
    elif method == "income":
        base_value = income_valuation
    else:
        candidates = [v for v in (ebitda_valuation, income_valuation) if v > 0]
        base_value = sum(candidates) / len(candidates) if candidates else 0

    low = base_value * 0.9
    high = base_value * 1.1

    factors = [
        (f"Odvetvie: {industry}", f"základný násobok {base_multiple:.2f}×"),
        ("Roky podnikania", years_note),
        ("EBITDA marža", margin_note),
    ]

    return {
        "ebitda_valuation": ebitda_valuation,
        "income_valuation": income_valuation,
        "adjusted_multiple": adjusted_multiple,
        "cap_rate": cap_rate,
        "range_low": low,
        "range_high": high,
        "factors": factors,
    }


def format_eur(value):
    return f"{value:,.2f} €".replace(",", " ")


def main_app():
    st.title("Indikatívne ocenenie spoločnosti")
    st.caption("Rýchly odhad trhovej hodnoty vašej firmy na základe pár základných údajov.")

    with st.sidebar:
        st.subheader("O nástroji")
        st.write(
            "Tento nástroj vznikol ako case study pre pohovor v KPMG. "
            "Poskytuje rýchly indikatívny odhad trhovej hodnoty malej "
            "firmy na základe zjednodušeného oceňovacieho modelu."
        )
        st.write("Autor: Adrián Textor")
        st.divider()
        st.write(f"Prihlásený ako: **{DEMO_USERNAME}**")
        if st.button("Odhlásiť sa"):
            st.session_state["logged_in"] = False
            st.rerun()

    with st.expander("Ako nástroj počíta hodnotu firmy"):
        st.markdown(
            "Nástroj kombinuje dva bežne používané zjednodušené prístupy:\n\n"
            "**Násobok EBITDA** - vynásobí prevádzkový zisk pred odpismi a "
            "úrokmi (EBITDA) typickým násobkom pre dané odvetvie. Násobok sa "
            "upravuje podľa počtu rokov podnikania a podľa EBITDA marže "
            "(pomer EBITDA k tržbám) - efektívnejšia firma s vyššou maržou "
            "dosahuje vyššie ocenenie.\n\n"
            "**Kapitalizácia zisku** - vydelí čistý zisk mierou kapitalizácie "
            "typickou pre dané odvetvie (čím rizikovejší biznis, tým vyššia "
            "miera, a teda nižšia vypočítaná hodnota).\n\n"
            "Podľa zvolenej metódy nástroj použije jednu z nich, alebo obe "
            "skombinuje. Výsledok je vždy rozpätie s bezpečnostnou rezervou "
            "±10 %, nie jedno presné číslo.\n\n"
            "Odvetvové násobky aj miery kapitalizácie sú v tejto verzii "
            "ilustračné hodnoty - v reálnom nasadení by pochádzali z "
            "databázy aktuálnych trhových transakcií."
        )

    st.divider()
    st.subheader("1. Zadajte základné údaje o firme")

    with st.form("valuation_form"):
        company_name = st.text_input(
            "Názov spoločnosti (nepovinné)",
            help="Ak ho zadáte, zobrazí sa vo výsledku ocenenia.",
        )

        industry = st.selectbox("Odvetvie podnikania", list(INDUSTRY_MULTIPLES.keys()))

        method_label = st.selectbox(
            "Metóda ocenenia",
            list(METHOD_OPTIONS.keys()),
            help=(
                "Kombinácia oboch metód dáva vyváženejší odhad. Jednotlivé "
                "metódy sú vhodné, ak chcete vidieť, ako by ocenenie vyzeralo "
                "len z pohľadu prevádzkového zisku, alebo len z pohľadu "
                "čistého zisku."
            ),
        )

        col1, col2 = st.columns(2)
        with col1:
            revenue = st.number_input(
                "Ročné tržby (€)",
                min_value=0.0, value=200000.0, step=1000.0, format="%.2f",
                help="Celkové ročné tržby spoločnosti pred akýmikoľvek odpočtami.",
            )
            ebitda = st.number_input(
                "EBITDA (€)",
                min_value=0.0, value=40000.0, step=1000.0, format="%.2f",
                help=(
                    "Prevádzkový zisk pred odpismi, úrokmi a daňami. Ak "
                    "nepoznáte presné číslo, použite hrubý odhad "
                    "prevádzkového zisku."
                ),
            )
        with col2:
            net_profit = st.number_input(
                "Čistý zisk po zdanení (€)",
                min_value=0.0, value=30000.0, step=1000.0, format="%.2f",
                help="Zisk, ktorý firme zostane po odpočítaní všetkých nákladov a daní.",
            )
            years_in_business = st.number_input(
                "Počet rokov podnikania",
                min_value=0.0, value=5.0, step=1.0, format="%.0f",
            )

        submitted = st.form_submit_button("Vypočítať ocenenie", type="primary")

    if submitted:
        errors, warnings = validate_inputs(revenue, ebitda, net_profit, years_in_business)

        if errors:
            for err in errors:
                st.error(err)
            return

        for warn in warnings:
            st.warning(warn)

        progress = st.progress(0, text="Počítam ocenenie...")
        for pct in (25, 55, 80, 100):
            time.sleep(0.12)
            progress.progress(pct, text="Počítam ocenenie...")
        time.sleep(0.15)
        progress.empty()

        method = METHOD_OPTIONS[method_label]
        result = calculate_valuation(
            revenue, ebitda, net_profit, industry, years_in_business, method
        )

        st.divider()
        st.subheader("2. Výsledok ocenenia")

        result_title = (
            f"Odhadovaná trhová hodnota - {company_name}"
            if company_name.strip()
            else "Odhadovaná trhová hodnota firmy"
        )

        st.metric(
            label=result_title,
            value=f"{format_eur(result['range_low'])} – {format_eur(result['range_high'])}",
        )

        st.info(
            "Toto je orientačný odhad na základe zjednodušeného modelu. "
            "Pre presné ocenenie - napríklad pri predaji firmy alebo vstupe "
            "investora - odporúčame konzultáciu s odborníkom na oceňovanie "
            "podnikov."
        )

        st.markdown("**Hlavné faktory, ktoré ovplyvnili výsledok:**")
        for label, note in result["factors"]:
            st.markdown(f"- **{label}**: {note}")

        if method == "combined" and result["ebitda_valuation"] > 0 and result["income_valuation"] > 0:
            st.markdown("**Porovnanie oboch metód**")
            chart_data = pd.DataFrame(
                {
                    "Metóda": ["Násobok EBITDA", "Kapitalizácia zisku"],
                    "Hodnota (€)": [
                        result["ebitda_valuation"],
                        result["income_valuation"],
                    ],
                }
            ).set_index("Metóda")
            st.bar_chart(chart_data)

        with st.expander("Detail výpočtu"):
            st.markdown(f"""
**Násobok EBITDA**
- Odvetvie: {industry} → základný násobok {INDUSTRY_MULTIPLES[industry]}×
- Upravený násobok (roky podnikania × EBITDA marža): **{result['adjusted_multiple']:.2f}×**
- Výpočet: EBITDA ({format_eur(ebitda)}) × {result['adjusted_multiple']:.2f}
- Výsledok: **{format_eur(result['ebitda_valuation'])}**

**Kapitalizácia čistého zisku**
- Miera kapitalizácie pre dané odvetvie: **{result['cap_rate'] * 100:.0f} %**
- Výpočet: Čistý zisk ({format_eur(net_profit)}) / {result['cap_rate'] * 100:.0f} %
- Výsledok: **{format_eur(result['income_valuation'])}**

**Finálne rozpätie**
Podľa zvolenej metódy ({method_label.lower()}) a s bezpečnostnou rezervou
±10 % dostávame odhadované rozpätie hodnoty.
            """)


def main():
    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False

    if st.session_state["logged_in"]:
        main_app()
    else:
        login_screen()


main()