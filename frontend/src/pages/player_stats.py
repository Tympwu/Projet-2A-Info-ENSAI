"""
Streamlit page for looking at stat about player.

Allows a player to look into someone else stat.

Endpoints used:
    GET /player
"""

import pandas as pd
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

    player = api_client.get(f"/player/{player_id}")["data"]

    st.subheader(player["username"])

    col1, col2, col3 = st.columns(3, border=True)
    with col1:
        (st.metric("Elo", player["elo"]))
    with col2:
        st.write(player["email"])
    with col3:
        st.checkbox("Pokemon fan", player["pokemon_fan"])

# Game

games = api_client.get(path="/game/", params={"id_player": player_id})["data"]

if not games:
    st.warning("There is no game linked with this player")
    st.stop()
else:
    df = pd.DataFrame([
        {
            "Mode": games[i]["game_mode"],
            "Opponent": games[i]["player1"]["username"]
            if games[i]["player1"]["id_player"] != player_id
            else games[i]["player2"]["username"],

            "Result": "Draw"
            if games[i]["winner"] is None
            else (
                "Win"
                if (games[i]["winner"]["id_player"] == int(player_id))
                else "Loss"
            ),
        }
        for i in range(len(games))
    ])

    st.dataframe(df, use_container_width=True)
