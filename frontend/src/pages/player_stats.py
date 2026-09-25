"""
Streamlit page for looking at stat about player.

Allows a player to look into someone else stat.

Endpoints used:
    GET /player
"""

import streamlit as st

from utils.api_client import api_client
from utils.log_init import get_page_logger

st.title("Player stat !")
logger = get_page_logger("player_stats")


if not st.query_params["id_player"].isnumeric():
    st.warning("Arguments not valid")
    st.stop()
else:
    player_id = st.query_params["id_player"]

player = api_client.get(path="/player/", params={"id_player": player_id})

st.write(f"/player?id_player={player_id}")
st.write(player)
