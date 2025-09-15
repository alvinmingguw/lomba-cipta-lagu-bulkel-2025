import streamlit as st

def render_playlist_audio_player(songs_data: list, player_key: str = "main_playlist"):
    """Render a playlist-style audio player similar to foobar2000"""
    
    # Initialize playlist state
    if f"{player_key}_current_track" not in st.session_state:
        st.session_state[f"{player_key}_current_track"] = 0
    if f"{player_key}_is_playing" not in st.session_state:
        st.session_state[f"{player_key}_is_playing"] = False
    
    if not songs_data:
        st.info("📭 Tidak ada lagu dalam playlist")
        return
    
    current_track_idx = st.session_state[f"{player_key}_current_track"]
    current_song = songs_data[current_track_idx] if current_track_idx < len(songs_data) else songs_data[0]
    
    # Main player header
    st.markdown("### 🎵 **Playlist Audio Player**")
    
    # Current track info and main controls
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 1rem;
            border-radius: 10px;
            margin-bottom: 0.5rem;
        ">
            <h4 style="margin: 0; font-size: 1.1rem;">🎵 {current_song.get('title', 'Unknown Title')}</h4>
            <p style="margin: 0.2rem 0 0 0; opacity: 0.9; font-size: 0.9rem;">
                👤 {current_song.get('composer', 'Unknown Artist')} | 
                🏆 Track {current_track_idx + 1}/{len(songs_data)}
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        # Previous/Next controls
        col_prev, col_next = st.columns(2)
        with col_prev:
            if st.button("⏮️", key=f"{player_key}_prev", help="Previous Track", use_container_width=True):
                if current_track_idx > 0:
                    st.session_state[f"{player_key}_current_track"] = current_track_idx - 1
                    st.rerun()
        with col_next:
            if st.button("⏭️", key=f"{player_key}_next", help="Next Track", use_container_width=True):
                if current_track_idx < len(songs_data) - 1:
                    st.session_state[f"{player_key}_current_track"] = current_track_idx + 1
                    st.rerun()
    
    with col3:
        # Shuffle and repeat (placeholder for now)
        col_shuffle, col_repeat = st.columns(2)
        with col_shuffle:
            st.button("🔀", key=f"{player_key}_shuffle", help="Shuffle (Coming Soon)", disabled=True, use_container_width=True)
        with col_repeat:
            st.button("🔁", key=f"{player_key}_repeat", help="Repeat (Coming Soon)", disabled=True, use_container_width=True)
    
    # Main audio player
    if current_song.get('audio_url'):
        st.audio(current_song['audio_url'], format='audio/mp3', start_time=0)
    else:
        st.warning("🔇 Audio tidak tersedia untuk track ini")
    
    # Playlist view
    with st.expander("📋 **Playlist** (Click to expand)", expanded=False):
        st.markdown("**🎵 All Tracks:**")
        
        for idx, song in enumerate(songs_data):
            # Highlight current track
            is_current = idx == current_track_idx
            bg_color = "#e3f2fd" if is_current else "#f9f9f9"
            border = "2px solid #2196F3" if is_current else "1px solid #ddd"
            
            col_track, col_play = st.columns([4, 1])
            
            with col_track:
                st.markdown(f"""
                <div style="
                    background-color: {bg_color};
                    border: {border};
                    border-radius: 8px;
                    padding: 0.5rem;
                    margin: 0.2rem 0;
                    cursor: pointer;
                ">
                    <strong>{'🎵 ' if is_current else '🎶 '}{song.get('title', 'Unknown Title')}</strong><br>
                    <small style="color: #666;">👤 {song.get('composer', 'Unknown Artist')}</small>
                </div>
                """, unsafe_allow_html=True)
            
            with col_play:
                if st.button("▶️" if not is_current else "⏸️", 
                           key=f"{player_key}_play_{idx}", 
                           help="Play this track" if not is_current else "Currently playing",
                           use_container_width=True):
                    if not is_current:
                        st.session_state[f"{player_key}_current_track"] = idx
                        st.rerun()

def render_tabs_layout_demo(songs_data: list):
    """Demo tabs layout for content"""
    st.markdown("### 🎵 **Tabs Layout Demo**")
    
    # Create tabs
    tab1, tab2, tab3 = st.tabs(["🎵 Audio", "📝 Syair + Chord", "📄 PDF Documents"])
    
    with tab1:
        st.markdown("**🎵 Audio Player**")
        if songs_data:
            current_song = songs_data[0]  # Demo with first song
            if current_song.get('audio_url'):
                st.audio(current_song['audio_url'], format='audio/mp3')
            else:
                st.info("🔇 Audio demo tidak tersedia")
    
    with tab2:
        st.markdown("**📝 Syair + Chord**")
        st.code("""
[Verse 1]
C                F
Dalam keluarga yang harmonis
G                C
Kasih mengalir tanpa henti
F                G
Bersama kita membangun
C                Am
Rumah tangga yang bahagia
        """, language="text")
    
    with tab3:
        st.markdown("**📄 PDF Documents**")
        st.info("📄 Demo PDF viewer akan muncul di sini")
        st.markdown("- 🎼 Notasi PDF Preview")
        st.markdown("- 📝 Syair PDF Preview")

# Main demo page
def main():
    st.set_page_config(
        page_title="Audio Playlist Player Demo",
        page_icon="🎵",
        layout="wide"
    )
    
    st.title("🎵 Audio Playlist Player Demo")
    st.markdown("---")
    
    # Sample data for demo
    demo_songs = [
        {
            "title": "Keluarga Harmonis",
            "composer": "John Doe",
            "audio_url": "https://www.soundjay.com/misc/sounds/bell-ringing-05.wav"  # Demo audio
        },
        {
            "title": "Kasih Keluarga",
            "composer": "Jane Smith", 
            "audio_url": "https://www.soundjay.com/misc/sounds/bell-ringing-05.wav"  # Demo audio
        },
        {
            "title": "Rumah Bahagia",
            "composer": "Bob Wilson",
            "audio_url": "https://www.soundjay.com/misc/sounds/bell-ringing-05.wav"  # Demo audio
        }
    ]
    
    # Layout selection
    layout_mode = st.selectbox(
        "🎛️ **Choose Layout Mode:**",
        ["Playlist Player", "Tabs Layout Demo"],
        index=0
    )
    
    st.markdown("---")
    
    if layout_mode == "Playlist Player":
        # Demo playlist player
        render_playlist_audio_player(demo_songs, "demo_playlist")
        
        st.markdown("---")
        st.markdown("### 📋 **Features:**")
        st.markdown("""
        - 🎵 **Main Player** dengan current track info
        - ⏮️⏭️ **Previous/Next** navigation
        - 📋 **Expandable Playlist** dengan semua tracks
        - 🎯 **Click to Play** any track dari playlist
        - 🎨 **Visual Feedback** untuk current playing track
        - 🔀🔁 **Shuffle/Repeat** (coming soon)
        """)
        
    else:
        # Demo tabs layout
        render_tabs_layout_demo(demo_songs)
        
        st.markdown("---")
        st.markdown("### 📋 **Tabs vs Expander:**")
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**✅ Tabs Advantages:**")
            st.markdown("""
            - Clean, space efficient
            - Easy navigation
            - Professional look
            - Single focus area
            """)
            
        with col2:
            st.markdown("**✅ Expander Advantages:**")
            st.markdown("""
            - Multiple sections open
            - Scroll friendly
            - More flexible
            - Current implementation
            """)

if __name__ == "__main__":
    main()
