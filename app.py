import streamlit as st

st.set_page_config(page_title="Ocenenie firmy", page_icon="💰", layout="centered")

# ---------------------------------------------------------------------------
# JEDNODUCHÁ "PRIHLASOVACIA" VRSTVA
# Poznámka: pre účely case study stačí demo login. Nie je to produkčná
# autentifikácia (žiadny hashing hesiel, žiadna DB) - dá sa to na pohovore
# otvorene povedať a vysvetliť, čo by sa spravilo inak v reálnej appke
# (napr. hashované heslá, OAuth, session management cez DB).
# ---------------------------------------------------------------------------

DEMO_USERNAME = "demo"
DEMO_PASSWORD = "demo123"

# Odvetvové násobky EBITDA (ilustračné, zjednodušené hodnoty)
# V reálnej appke by tieto čísla pochádzali z databázy trhových dát
# (napr. Damodaran multiples, lokálne M&A transakcie a pod.)
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


def login_screen():
    st.title("🔐 Prihlásenie")
    st.caption("Demo účet: **demo** / **demo123**")

    with st.form("login_form"):
        username = st.text_input("Používateľské meno")
        password = st.text_input("Heslo", type="password")
        submitted = st.form_submit_button("Prihlásiť sa")

        if submitted:
            if username == DEMO_USERNAME and password == DEMO_PASSWORD:
                st.session_state["logged_in"] = True
                st.rerun()
            else:
                st.error("Nesprávne meno alebo heslo. Skúste demo / demo123.")


def calculate_valuation(revenue, ebitda, net_profit, industry, years_in_business):
    """
    Vracia rozpätie hodnoty firmy na základe dvoch jednoduchých metód:
    1. Násobok EBITDA (Market approach - zjednodušený)
    2. Kapitalizácia čistého zisku (Income approach - zjednodušený)

    Toto NIE JE presné profesionálne ocenenie - ide o indikatívny odhad
    pre malých podnikateľov, ktorí nemajú prístup k detailnému M&A dátam.
    """
    # --- Metóda 1: Násobok EBITDA ---
    base_multiple = INDUSTRY_MULTIPLES[industry]

    # Jednoduchá úprava násobku podľa "vyzretosti" firmy
    # (viac rokov na trhu = o niečo nižšie vnímané riziko)
    if years_in_business >= 10:
        multiple_adjustment = 1.1
    elif years_in_business >= 5:
        multiple_adjustment = 1.0
    else:
        multiple_adjustment = 0.85

    adjusted_multiple = base_multiple * multiple_adjustment
    ebitda_valuation = ebitda * adjusted_multiple

    # --- Metóda 2: Kapitalizácia zisku ---
    cap_rate = CAP_RATES[industry]
    income_valuation = net_profit / cap_rate if cap_rate > 0 else 0

    # --- Výsledné rozpätie ---
    low = min(ebitda_valuation, income_valuation) * 0.9
    high = max(ebitda_valuation, income_valuation) * 1.1

    return {
        "ebitda_valuation": ebitda_valuation,
        "income_valuation": income_valuation,
        "adjusted_multiple": adjusted_multiple,
        "cap_rate": cap_rate,
        "range_low": low,
        "range_high": high,
    }


def format_eur(value):
    return f"{value:,.0f} €".replace(",", " ")


def main_app():
    st.title("💰 Indikatívne ocenenie spoločnosti")
    st.caption("Rýchly odhad trhovej hodnoty vašej firmy na základe pár základných údajov.")

    with st.sidebar:
        st.write(f"Prihlásený ako: **{DEMO_USERNAME}**")
        if st.button("Odhlásiť sa"):
            st.session_state["logged_in"] = False
            st.rerun()

    st.divider()
    st.subheader("1. Zadajte základné údaje o firme")

    with st.form("valuation_form"):
        industry = st.selectbox("Odvetvie podnikania", list(INDUSTRY_MULTIPLES.keys()))

        col1, col2 = st.columns(2)
        with col1:
            revenue = st.number_input(
                "Ročné tržby (€)", min_value=0, value=200000, step=10000
            )
            ebitda = st.number_input(
                "EBITDA (prevádzkový zisk pred odpismi a úrokmi, €)",
                min_value=0, value=40000, step=5000,
                help="Ak neviete presné EBITDA, môžete použiť odhad prevádzkového zisku."
            )
        with col2:
            net_profit = st.number_input(
                "Čistý zisk po zdanení (€)", min_value=0, value=30000, step=5000
            )
            years_in_business = st.number_input(
                "Počet rokov podnikania", min_value=0, value=5, step=1
            )

        submitted = st.form_submit_button("Vypočítať ocenenie", type="primary")

    if submitted:
        if ebitda == 0 and net_profit == 0:
            st.warning("Zadajte prosím aspoň jednu z hodnôt EBITDA alebo čistý zisk väčšiu ako 0.")
            return

        result = calculate_valuation(revenue, ebitda, net_profit, industry, years_in_business)

        st.divider()
        st.subheader("2. Výsledok ocenenia")

        st.metric(
            label="Odhadovaná trhová hodnota firmy (rozpätie)",
            value=f"{format_eur(result['range_low'])} – {format_eur(result['range_high'])}",
        )

        st.info(
            "⚠️ Toto je **orientačný odhad** na základe zjednodušeného modelu. "
            "Pre presné ocenenie (napr. pri predaji firmy alebo vstupe investora) "
            "odporúčame konzultáciu s odborníkom na oceňovanie podnikov."
        )

        with st.expander("📊 Ako sme sa k číslu dopracovali? (detail výpočtu)"):
            st.markdown(f"""
**Metóda 1: Násobok EBITDA**
- Odvetvie: {industry} → základný násobok {INDUSTRY_MULTIPLES[industry]}×
- Upravený násobok podľa počtu rokov podnikania: **{result['adjusted_multiple']:.2f}×**
- Výpočet: EBITDA ({format_eur(ebitda)}) × {result['adjusted_multiple']:.2f}
- **Výsledok: {format_eur(result['ebitda_valuation'])}**

**Metóda 2: Kapitalizácia čistého zisku**
- Miera kapitalizácie pre dané odvetvie: **{result['cap_rate']*100:.0f}%**
- Výpočet: Čistý zisk ({format_eur(net_profit)}) / {result['cap_rate']*100:.0f}%
- **Výsledok: {format_eur(result['income_valuation'])}**

**Finálne rozpätie**
Kombináciou oboch metód (s bezpečnostnou rezervou ±10 %) dostávame odhadované rozpätie hodnoty.
            """)


def main():
    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False

    if st.session_state["logged_in"]:
        main_app()
    else:
        login_screen()


main()
