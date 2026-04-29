import streamlit as st
import pandas as pd
import os
import shutil
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go

# --- App Configuration & Roster ---
st.set_page_config(page_title="MLB The Show 26 Tracker", layout="wide")
st.title("⚾ MLB The Show 26 Co-op Tracker")

# THE OFFICIAL LEAGUE ROSTER
ROSTER = ["Ernest", "Landon", "Caleb", "Roman", "Troy"]

DATA_FILE = "mlb_show_stats.csv"

# --- Data Management ---
def load_data():
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
        
        if 'Date' not in df.columns:
            df.insert(0, 'Date', "Legacy Record")
            
        if not df.empty:
            df['Game WAR'] = (df['Hits'] * 0.5) + (df['TB'] * 0.25) + (df['Walks'] * 0.5) + (df['RBIs'] * 1.0) - (df['ERA_Plus'] * 0.5)
        return df
    else:
        cols = ["Date", "Player", "Hits", "Walks", "RBIs", "HR", "xBH", "TB", "ERA_Plus"]
        return pd.DataFrame(columns=cols)

def save_game(player, hits, walks, rbis, hr, xbh, tb, era_plus):
    df = load_data()
    if 'Game WAR' in df.columns:
        df = df.drop(columns=['Game WAR'])
        
    game_date = datetime.now().strftime("%b %d, %Y")
    new_game = pd.DataFrame([[game_date, player, hits, walks, rbis, hr, xbh, tb, era_plus]], columns=df.columns)
    df = pd.concat([df, new_game], ignore_index=True)
    
    df.to_csv(DATA_FILE, index=False)
    
    timestamp = datetime.now().strftime("%Y%m%d")
    shutil.copy(DATA_FILE, f"backup_stats_{timestamp}.csv")
    st.success(f"Game logged successfully for {player}!")

def filter_games(df, timeframe):
    if timeframe == "Last 3 Games":
        return df.groupby('Player').tail(3)
    elif timeframe == "Last 5 Games":
        return df.groupby('Player').tail(5)
    elif timeframe == "Last 10 Games":
        return df.groupby('Player').tail(10)
    return df

df = load_data()
timeframe_options = ["All Games", "Last 3 Games", "Last 5 Games", "Last 10 Games"]

# --- Tabs Setup ---
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["📝 Input Stats", "🏆 Standings", "📈 Trends", "⚔️ Head-to-Head", "🎖️ Records", "📅 Game Logs"])

# --- TAB 1: Input Stats ---
with tab1:
    st.header("Log a New Game")
    with st.form("game_form", clear_on_submit=True):
        # ---> IDIOT-PROOF DROPDOWN HERE <---
        player = st.selectbox("Player", ROSTER, index=None, placeholder="⚠️ SELECT A PLAYER ⚠️")
        
        col1, col2, col3, col4 = st.columns(4)
        hits = col1.number_input("Hits", min_value=0, step=1)
        tb = col2.number_input("Total Bases (TB)", min_value=0, step=1)
        xbh = col3.number_input("Extra Base Hits (xBH)", min_value=0, step=1)
        hr = col4.number_input("Home Runs", min_value=0, step=1)
        
        col5, col6, col7 = st.columns(3)
        walks = col5.number_input("Walks", min_value=0, step=1)
        rbis = col6.number_input("RBIs", min_value=0, step=1)
        era_plus = col7.number_input("Pitching Runs Allowed (ERA+)", min_value=0.0, step=0.5)
        
        if st.form_submit_button("Submit Game Log"):
            if player is None:
                st.error("🚨 Stop! You forgot to select a player!")
            else:
                save_game(player, hits, walks, rbis, hr, xbh, tb, era_plus)
                st.rerun()

# --- TAB 2: Standings ---
with tab2:
    col_filter, _ = st.columns([1, 3])
    timeframe = col_filter.selectbox("Timeframe Filter", timeframe_options, key="standings_time")
    
    f_df = filter_games(df, timeframe)
    
    if not f_df.empty:
        sums = f_df.groupby('Player').sum(numeric_only=True).reset_index()
        counts = f_df.groupby('Player').size().reset_index(name='GP')
        stats = pd.merge(sums, counts, on='Player')
    else:
        stats = pd.DataFrame(columns=['Player', 'Hits', 'Walks', 'RBIs', 'HR', 'xBH', 'TB', 'ERA_Plus', 'GP'])
        
    roster_df = pd.DataFrame({'Player': ROSTER})
    totals = pd.merge(roster_df, stats, on='Player', how='left').fillna(0)
    
    totals['wRC'] = totals['TB'] + totals['Walks'] + totals['RBIs']
    totals['wRC+'] = (totals['wRC'] / totals['GP']).fillna(0).round(2)
    totals['Pitching Penalty'] = (totals['ERA_Plus'] * 0.5).round(2)
    off_war = (totals['Hits'] * 0.5) + (totals['TB'] * 0.25) + (totals['Walks'] * 0.5) + (totals['RBIs'] * 1.0)
    
    totals['Cum. WAR'] = (off_war - totals['Pitching Penalty']).round(2)
    totals['WAR Avg'] = (totals['Cum. WAR'] / totals['GP']).fillna(0).round(2)
    
    totals['Hits/G'] = (totals['Hits'] / totals['GP']).fillna(0).round(2)
    totals['TB/G'] = (totals['TB'] / totals['GP']).fillna(0).round(2)
    totals['HR/G'] = (totals['HR'] / totals['GP']).fillna(0).round(2)
    totals['RBI/G'] = (totals['RBIs'] / totals['GP']).fillna(0).round(2)
    
    st.subheader("MVP Race (Advanced Metrics)")
    adv_cols = ['Player', 'GP', 'wRC', 'wRC+', 'Pitching Penalty', 'Cum. WAR', 'WAR Avg']
    st.dataframe(totals[adv_cols].sort_values(by="Cum. WAR", ascending=False), use_container_width=True, hide_index=True)
    
    st.subheader("Box Score (Standard Stats & Averages)")
    std_cols = ['Player', 'GP', 'Hits', 'Hits/G', 'TB', 'TB/G', 'HR', 'HR/G', 'RBIs', 'RBI/G']
    st.dataframe(totals[std_cols].sort_values(by="TB", ascending=False), use_container_width=True, hide_index=True)

# --- TAB 3: Trends ---
with tab3:
    st.header("Momentum & Hot Streaks")
    
    col_t, _ = st.columns([1, 3])
    trend_time = col_t.selectbox("Chart Timeframe", timeframe_options, key="chart_time")
    
    if not df.empty:
        df['Game Number'] = df.groupby('Player').cumcount() + 1
        df['Running Cumulative WAR'] = df.groupby('Player')['Game WAR'].cumsum()
        df['Game WAR (Delta)'] = df['Game WAR'].apply(lambda x: f"+{x:.2f} WAR" if x > 0 else f"{x:.2f} WAR")
        
        trend_df = filter_games(df, trend_time)
        
        fig = px.line(trend_df, x="Game Number", y="Running Cumulative WAR", color="Player", 
                      hover_data={"Player": False, "Game Number": False, "Running Cumulative WAR": ':.2f', "Game WAR (Delta)": True},
                      title="Cumulative WAR Progression", markers=True, template="plotly_dark")
        
        fig.update_traces(hovertemplate="<b>%{data.name}</b><br>Game %{x}<br>Total WAR: %{y:.2f}<br>Game Perf: %{customdata[0]}<extra></extra>")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Log a game to see the trend lines!")

# --- TAB 4: Head-to-Head ---
with tab4:
    st.header("Direct Comparison")
    
    col_f, _ = st.columns([1, 3])
    h2h_time = col_f.selectbox("Timeframe", timeframe_options, key="h2h_time")
    
    col1, col2 = st.columns(2)
    p1 = col1.selectbox("Player 1", ROSTER, index=0)
    p2 = col2.selectbox("Player 2", ROSTER, index=1 if len(ROSTER)>1 else 0)
    
    if p1 != p2:
        h2h_df = filter_games(df, h2h_time)
        p1_data = h2h_df[h2h_df['Player'] == p1].mean(numeric_only=True).fillna(0)
        p2_data = h2h_df[h2h_df['Player'] == p2].mean(numeric_only=True).fillna(0)
        
        p1_wrc = p1_data.get('TB', 0) + p1_data.get('Walks', 0) + p1_data.get('RBIs', 0)
        p2_wrc = p2_data.get('TB', 0) + p2_data.get('Walks', 0) + p2_data.get('RBIs', 0)
        
        metrics = ["Hits/G", "TB/G", "HR/G", "RBI/G", "wRC+ (Avg)"]
        p1_vals = [p1_data.get('Hits', 0), p1_data.get('TB', 0), p1_data.get('HR', 0), p1_data.get('RBIs', 0), p1_wrc]
        p2_vals = [p2_data.get('Hits', 0), p2_data.get('TB', 0), p2_data.get('HR', 0), p2_data.get('RBIs', 0), p2_wrc]
        
        fig2 = go.Figure(data=[
            go.Bar(name=p1, x=metrics, y=p1_vals),
            go.Bar(name=p2, x=metrics, y=p2_vals)
        ])
        fig2.update_layout(barmode='group', title=f"{p1} vs {p2} (Per Game Averages)", template="plotly_dark")
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.warning("Select two different players to compare.")

# --- TAB 5: Records ---
with tab5:
    st.markdown("## 🏆 League Records & Hall of Shame")
    st.markdown("---")
    
    if not df.empty:
        st.markdown("""
        <style>
        .record-card {
            background-color: rgba(128, 128, 128, 0.1);
            border-radius: 10px;
            padding: 15px;
            margin-bottom: 20px;
            border-left: 5px solid;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        .fame-card { border-left-color: #00CC96; }
        .shame-card { border-left-color: #EF553B; }
        .record-title { color: #888; font-size: 13px; font-weight: bold; margin-bottom: 5px; text-transform: uppercase; letter-spacing: 1px;}
        .record-player { font-size: 24px; font-weight: bold; margin: 0; line-height: 1.2;}
        .record-val { font-size: 18px; opacity: 0.8; font-weight: normal;}
        .record-date { color: #888; font-size: 12px; margin-top: 8px; font-style: italic; }
        </style>
        """, unsafe_allow_html=True)
        
        # ---> NEW TIE-BREAKER LOGIC HERE <---
        def render_card(title, col_name, is_shame=False, fmt="{}", is_min=False):
            target_val = df[col_name].min() if is_min else df[col_name].max()
            tied_rows = df[df[col_name] == target_val]
            
            # Find all players tied for the record
            tied_players = tied_rows['Player'].unique().tolist()
            player_str = ", ".join(tied_players)
            
            val_str = fmt.format(target_val)
            
            # If multiple dates tied, label it "Multiple Occurrences"
            if len(tied_rows) == 1:
                date_str = f"📅 {tied_rows['Date'].iloc[0]}"
            else:
                date_str = "📅 Multiple Occurrences"
            
            card_class = "shame-card" if is_shame else "fame-card"
            
            html = f"""
            <div class="record-card {card_class}">
                <div class="record-title">{title}</div>
                <div class="record-player">{player_str} <span class="record-val">({val_str})</span></div>
                <div class="record-date">{date_str}</div>
            </div>
            """
            st.markdown(html, unsafe_allow_html=True)

        col1, col_gap, col2 = st.columns([1, 0.1, 1])
        
        with col1:
            st.subheader("⭐ The Hall of Fame")
            render_card("Highest Single-Game WAR", 'Game WAR', fmt="{:.2f}")
            render_card("Most Single Game Hits", 'Hits')
            render_card("Most Single Game Home Runs", 'HR')
            render_card("Most Single Game RBIs (The Clutch King)", 'RBIs')
            render_card("Most Single Game Total Bases", 'TB')

        with col2:
            st.subheader("💀 The Hall of Shame")
            render_card("Worst Single-Game WAR", 'Game WAR', is_shame=True, fmt="{:.2f}", is_min=True)
            render_card("Most Single Game Runs Allowed  (BP Pitcher)", 'ERA_Plus', is_shame=True, fmt="{:.1f}")
            render_card("Most Single Game Walks", 'Walks', is_shame=True)
            
    else:
        st.info("Log a game to populate the league records!")

# --- TAB 6: Game Logs ---
with tab6:
    st.header("📅 Player Game Logs")
    
    if not df.empty:
        col_f, _ = st.columns([1, 3])
        log_player = col_f.selectbox("Filter by Player", ["All Players"] + ROSTER, key="log_player")
        
        display_df = df.copy().iloc[::-1]
        
        if log_player != "All Players":
            display_df = display_df[display_df['Player'] == log_player]
            
        if 'Game WAR' in display_df.columns:
            display_df['Game WAR'] = display_df['Game WAR'].map('{:.2f}'.format)
            
        st.dataframe(display_df, use_container_width=True, hide_index=True)
    else:
        st.info("Log your first game to start building the history ledger!")