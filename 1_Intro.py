import streamlit as st

st.set_page_config(page_title="Data Science Project", page_icon="😊")

# Title of the app
st.title("Välkommen till den Svenska Händelse- och Väderinsiktsappen!")
st.subheader("🚓 Polisen API")
st.write(
    """            Denna app är utformad för att ge omfattande insikter om händelser som rapporteras över hela Sverige, baserat på data från polisens API. 
            Datainsamlingen började den 14 september och uppdateras dagligen kl. 13:00. Även om API
            kanske inte fångar upp varje händelse kan du enkelt filtrera rapporterna efter kategori, plats och datum för att hitta den information du söker. 
         """
)
st.subheader("📊 Analysera Händelser")
st.write(
    """
          Det finns också en analyssida där du kan få  djupare insikter i de rapporterade händelserna.
         
         """
)
st.subheader("🌦️ Väder och Körsäkerhet")
st.write(
    """
            Utöver händelserapporter erbjuder appen också körsäkerhet i realtid och väderinsikter, baserat på data från SMHI
            API. Du kan filtrera väderdata per plats för att bedöma om körförhållandena är bra, dåliga eller måttliga (mer information finns på vädersidan).
            Dessutom har du möjlighet att dela dina egna uppdateringar i sektionen för "Live Trafikuppdateringar" om vägläget var du än befinner dig i Sverige, vilket hjälper till att hålla samhället 
            informerat.
         """
)
