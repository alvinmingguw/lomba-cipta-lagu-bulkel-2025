"""
Super Admin Panel
Login as Juri + Admin Dashboard
"""

import streamlit as st
import pandas as pd
from services.auth_service import auth_service
from services.cache_service import cache_service
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

def render_admin_panel(admin_user):
    """Render super admin panel"""
    
    # Custom CSS for admin panel
    st.markdown("""
    <style>
    .admin-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 15px;
        color: white;
        margin-bottom: 2rem;
    }
    
    .admin-title {
        font-size: 2rem;
        font-weight: bold;
        margin-bottom: 0.5rem;
    }
    
    .admin-subtitle {
        opacity: 0.9;
        font-size: 1.1rem;
    }
    
    .impersonation-box {
        background: linear-gradient(135deg, #ff6b6b 0%, #feca57 100%);
        padding: 1.5rem;
        border-radius: 15px;
        color: white;
        margin-bottom: 2rem;
    }
    
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        text-align: center;
        margin-bottom: 1rem;
    }
    
    .metric-value {
        font-size: 2.5rem;
        font-weight: bold;
        color: #667eea;
    }
    
    .metric-label {
        font-size: 1rem;
        color: #666;
        margin-top: 0.5rem;
    }
    
    .stButton > button {
        border-radius: 10px;
        border: none;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .danger-btn {
        background-color: #ff4757 !important;
        color: white !important;
    }
    
    .success-btn {
        background-color: #2ed573 !important;
        color: white !important;
    }
    
    .warning-btn {
        background-color: #ffa502 !important;
        color: white !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Admin header
    st.markdown(f"""
    <div class="admin-header">
        <div class="admin-title">👑 Super Admin Panel</div>
        <div class="admin-subtitle">Welcome back, {admin_user.get('judges', {}).get('name', 'Admin')}!</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Check if currently impersonating
    if auth_service.is_impersonating():
        render_impersonation_status()
    else:
        render_admin_dashboard(admin_user)

def render_impersonation_status():
    """Show impersonation status and controls"""
    current_user = auth_service.get_current_user()
    impersonation_data = st.session_state.get('admin_impersonation', {})
    admin_user = impersonation_data.get('admin_user', {})

    st.markdown(f"""
    <div class="impersonation-box">
        <h3>🎭 Currently Impersonating</h3>
        <p><strong>Acting as:</strong> {current_user.get('judges', {}).get('name', 'Unknown Judge')}</p>
        <p><strong>Original Admin:</strong> {admin_user.get('judges', {}).get('name', 'Unknown Admin')}</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1, 1])

    with col2:
        if st.button("🔙 Return to Admin", key="end_impersonation", help="Stop impersonating and return to admin"):
            auth_service.end_impersonation()

def render_admin_dashboard(admin_user):
    """Render main admin dashboard with organized tabs"""

    # Judge impersonation is handled in main app.py - no need to duplicate here

    # Create main tabs for admin panel (removed Recent Activity tab)
    tab1, tab2, tab3 = st.tabs([
        "📊 Dashboard Overview",
        "👨‍⚖️ Judge Management",
        "⚙️ Configuration Management"
    ])

    # Get data for all tabs
    judges_df = cache_service.get_cached_judges()
    songs_df = cache_service.get_cached_songs()
    evaluations_df = cache_service.get_cached_evaluations()

    with tab1:
        render_dashboard_overview_tab(judges_df, songs_df, evaluations_df, admin_user)

    with tab2:
        render_judge_management_tab()

    with tab3:
        render_configuration_management_tab()

# Judge impersonation is now handled centrally in app.py - no duplication needed

def render_dashboard_overview_tab(judges_df, songs_df, evaluations_df, admin_user):
    """Render dashboard overview tab"""



    # Dashboard metrics
    st.markdown("### 📊 System Metrics")

    # Metrics row
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{len(judges_df)}</div>
            <div class="metric-label">Total Judges</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{len(songs_df)}</div>
            <div class="metric-label">Total Songs</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{len(evaluations_df)}</div>
            <div class="metric-label">Total Evaluations</div>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        completion_rate = calculate_completion_rate(judges_df, songs_df, evaluations_df)
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{completion_rate:.1f}%</div>
            <div class="metric-label">Completion Rate</div>
        </div>
        """, unsafe_allow_html=True)

    # Charts section
    col1, col2 = st.columns(2)

    with col1:
        render_evaluation_progress_chart(judges_df, songs_df, evaluations_df)

    with col2:
        render_judge_activity_chart(judges_df, evaluations_df)

    # Admin actions
    st.markdown("### 🔧 Admin Actions")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("🔄 Clear Cache", key="clear_cache", help="Clear all cached data"):
            cache_service.invalidate_cache()
            st.success("Cache cleared!")
            st.rerun()

    with col2:
        if st.button("📊 Export Data", key="export_data", help="Export all evaluation data"):
            export_all_data()

    with col3:
        if st.button("🚪 Logout", key="admin_logout", help="Logout from admin account"):
            auth_service.logout()



def render_judge_management_tab():
    """Render judge management tab"""
    st.markdown("### 👨‍⚖️ Judge Management")
    render_judge_management()

def render_configuration_management_tab():
    """Render configuration management tab"""
    st.markdown("### ⚙️ Configuration Management")
    render_configuration_management()

def calculate_completion_rate(judges_df, songs_df, evaluations_df):
    """Calculate evaluation completion rate"""
    if judges_df.empty or songs_df.empty:
        return 0.0
    
    total_possible = len(judges_df) * len(songs_df)
    total_completed = len(evaluations_df)
    
    return (total_completed / total_possible) * 100 if total_possible > 0 else 0.0

def render_evaluation_progress_chart(judges_df, songs_df, evaluations_df):
    """Render evaluation progress chart"""
    st.markdown("**📊 Evaluation Progress by Judge**")
    
    if not evaluations_df.empty and not judges_df.empty:
        # Count evaluations per judge
        eval_counts = evaluations_df.groupby('judge_id').size().reset_index(name='evaluations')
        
        # Merge with judge names
        progress_data = judges_df.merge(eval_counts, left_on='id', right_on='judge_id', how='left')
        progress_data['evaluations'] = progress_data['evaluations'].fillna(0)
        progress_data['total_songs'] = len(songs_df)
        progress_data['completion_rate'] = (progress_data['evaluations'] / progress_data['total_songs']) * 100
        
        fig = px.bar(
            progress_data,
            x='name',
            y='completion_rate',
            title="Completion Rate by Judge (%)",
            color='completion_rate',
            color_continuous_scale='viridis'
        )
        fig.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig, width=True)
    else:
        st.info("No evaluation data available yet")

def render_judge_activity_chart(judges_df, evaluations_df):
    """Render judge activity chart"""
    st.markdown("**👨‍⚖️ Judge Activity**")
    
    if not evaluations_df.empty and not judges_df.empty:
        # Count evaluations per judge
        activity_data = evaluations_df.groupby('judge_id').size().reset_index(name='evaluations')
        activity_data = judges_df.merge(activity_data, left_on='id', right_on='judge_id', how='left')
        activity_data['evaluations'] = activity_data['evaluations'].fillna(0)
        
        fig = px.pie(
            activity_data,
            values='evaluations',
            names='name',
            title="Evaluations by Judge"
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, width=True)
    else:
        st.info("No activity data available yet")



def render_judge_management():
    """Render judge management interface"""

    # Get current judges
    try:
        judges_df = auth_service.get_all_judges()
    except Exception as e:
        st.error(f"Error loading judges: {e}")
        return

    # Add new judge section
    with st.expander("➕ Add New Judge", expanded=False):
        col1, col2 = st.columns([2, 1])

        with col1:
            new_name = st.text_input("Judge Name", placeholder="John Doe", key="new_judge_name")
            new_email = st.text_input("Email Address", placeholder="judge@example.com", key="new_judge_email")

        with col2:
            new_role = st.selectbox("Role", ["judge", "admin"], key="new_judge_role")

        if st.button("➕ Add Judge", key="add_judge"):
            if new_name and new_email:
                # Check if email already exists
                existing_judge = judges_df[judges_df['email'].str.lower() == new_email.lower()]
                if not existing_judge.empty:
                    st.error(f"❌ Email {new_email} already exists for judge: {existing_judge.iloc[0]['name']}")
                elif auth_service.add_authorized_judge(new_name, new_email, new_role):
                    st.success(f"✅ Judge {new_name} added!")
                    cache_service.invalidate_cache()  # Clear cache
                    st.rerun()
                else:
                    st.error("❌ Failed to add judge")
            else:
                st.error("Please enter both name and email")

    # Current judges
    st.markdown("**👨‍⚖️ Current Judges:**")

    if not judges_df.empty:
        # Display judges with management options
        for idx, judge in judges_df.iterrows():
            col1, col2, col3, col4, col5 = st.columns([2, 2, 1, 1, 1])

            with col1:
                st.text(judge['name'])
            with col2:
                email = judge.get('email', 'No email')
                if email:
                    st.text(email)
                else:
                    st.text("❌ No email (can't login)")
            with col3:
                st.text(judge.get('role', 'judge').title())
            with col4:
                status = "✅ Active" if judge.get('is_active', False) else "❌ Inactive"
                st.text(status)
            with col5:
                # Edit button
                if st.button("✏️", key=f"edit_{judge['id']}", help=f"Edit {judge['name']}"):
                    st.session_state[f"editing_{judge['id']}"] = True
                    st.rerun()

            # Edit form (if editing)
            if st.session_state.get(f"editing_{judge['id']}", False):
                with st.container():
                    st.markdown(f"**Editing: {judge['name']}**")

                    # Form fields
                    col_name, col_email = st.columns(2)
                    col_role, col_status = st.columns(2)
                    col_save, col_delete, col_cancel = st.columns([1, 1, 1])

                    with col_name:
                        new_name = st.text_input(
                            "Name",
                            value=judge.get('name', ''),
                            key=f"edit_name_{judge['id']}"
                        )

                    with col_email:
                        new_email = st.text_input(
                            "Email",
                            value=judge.get('email', ''),
                            key=f"edit_email_{judge['id']}"
                        )

                    with col_role:
                        current_role = judge.get('role', 'judge')
                        new_role = st.selectbox(
                            "Role",
                            options=['judge', 'admin'],
                            index=0 if current_role == 'judge' else 1,
                            key=f"edit_role_{judge['id']}"
                        )

                    with col_status:
                        current_status = judge.get('is_active', True)
                        new_status = st.selectbox(
                            "Status",
                            options=[True, False],
                            format_func=lambda x: "Active" if x else "Inactive",
                            index=0 if current_status else 1,
                            key=f"edit_status_{judge['id']}"
                        )

                    with col_save:
                        if st.button("💾 Save", key=f"save_{judge['id']}", help="Save changes"):
                            success = True

                            # Update name if changed
                            if new_name != judge.get('name', ''):
                                if not auth_service.update_judge_name(judge['id'], new_name):
                                    success = False

                            # Update email if changed
                            if new_email != judge.get('email', ''):
                                if not auth_service.update_judge_email(judge['id'], new_email):
                                    success = False

                            # Update role if changed
                            if new_role != judge.get('role', 'judge'):
                                if not auth_service.update_judge_role(judge['id'], new_role):
                                    success = False

                            # Update status if changed
                            if new_status != judge.get('is_active', True):
                                if not auth_service.update_judge_status(judge['id'], new_status):
                                    success = False

                            if success:
                                st.success("✅ Updated!")
                                del st.session_state[f"editing_{judge['id']}"]
                                cache_service.invalidate_cache()  # Clear cache
                                st.rerun()
                            else:
                                st.error("❌ Failed to update")

                    with col_delete:
                        if st.button("🗑️ Delete", key=f"delete_{judge['id']}", help="Delete judge"):
                            if auth_service.delete_judge(judge['id']):
                                st.success("✅ Deleted!")
                                del st.session_state[f"editing_{judge['id']}"]
                                cache_service.invalidate_cache()  # Clear cache
                                st.rerun()
                            else:
                                st.error("❌ Failed to delete")

                    with col_cancel:
                        if st.button("❌ Cancel", key=f"cancel_{judge['id']}", help="Cancel"):
                            del st.session_state[f"editing_{judge['id']}"]
                            st.rerun()

                st.markdown("---")
    else:
        st.info("No judges found")

def render_configuration_management():
    """Render configuration management interface"""

    # Get current configuration
    try:
        from services.database_service import db_service
        config_df = db_service.get_configuration()
    except Exception as e:
        st.error(f"Error loading configuration: {e}")
        return

    # Calculate expected configurations dynamically
    expected_configs_count = {
        # Contest Settings
        'THEME', 'FORM_OPEN', 'SUBMISSION_START_DATETIME', 'SUBMISSION_END_DATETIME',
        'FORM_OPEN_DATETIME', 'FORM_CLOSE_DATETIME', 'WINNER_ANNOUNCE_DATETIME',
        'WINNERS_TOP_N', 'SHOW_WINNERS_AUTOMATIC', 'TIMEZONE',

        # Display Settings
        'SHOW_NILAI_CHIP', 'SHOW_AUTHOR', 'DEFAULT_TEXT_VIEW',
        'RUBRIK_INPUT_STYLE', 'SLIDER_LAYOUT', 'REQUIRE_CONFIRM_PANEL',
        'WINNER_DISPLAY_LAYOUT', 'SHOW_PDF_DOCUMENTS', 'SHOW_WINNER_SCORES', 'SHOW_ALL_SONGS_SCORES',

        # System Settings
        'CERTIFICATE_MODE', 'CERTIFICATE_BUCKET', 'CERTIFICATE_FOLDER',
        'LOCK_FINAL_EVALUATIONS', 'DETECT_CHORDS_FALLBACK',

        # Certificate Settings
        'CERTIFICATE_LIST_MODE', 'CERTIFICATE_PARTICIPANTS', 'CERTIFICATE_PARTICIPANT_MAPPING',
        'CERT_TEMPLATE_PARTICIPANT', 'CERT_TEMPLATE_WINNER', 'CERT_TEXT_COLOR_HEX',

        # Scoring & Analysis Settings
        'CHORD_SOURCE_PRIORITY', 'DISPLAY_TEXT_PRIORITY', 'LYRICS_SCORE_PRIORITY', 'THEME_SCORE_PRIORITY',
        'HARM_W_EXT', 'HARM_W_NONDI', 'HARM_W_SLASH', 'HARM_W_TRANS', 'HARM_W_UNIQ',

        # System Integration
        'DRIVE_FOLDER_ROOT_ID'
    }

    # Show configuration summary
    st.info(f"📊 **Total Configurations:** {len(config_df)} | **Expected:** {len(expected_configs_count)} configurations")

    # Configuration sections
    tabs = st.tabs(["🎯 Contest Settings", "🎨 Display Settings", "🔧 System Settings", "🏆 Certificate Settings", "⚙️ Advanced Settings", "🧹 Cleanup"])

    with tabs[0]:  # Contest Settings
        st.markdown("**Contest Configuration**")

        contest_configs = config_df[config_df['key'].isin([
            'THEME', 'FORM_OPEN', 'SUBMISSION_START_DATETIME', 'SUBMISSION_END_DATETIME',
            'FORM_OPEN_DATETIME', 'FORM_CLOSE_DATETIME', 'WINNER_ANNOUNCE_DATETIME',
            'WINNERS_TOP_N', 'SHOW_WINNERS_AUTOMATIC', 'TIMEZONE'
        ])]

        for _, config in contest_configs.iterrows():
            col1, col2 = st.columns([1, 2])

            with col1:
                st.text(config['key'])
                if config.get('description'):
                    st.caption(config['description'])

            with col2:
                key = f"config_{config['key']}"

                # Handle different input types
                if config['key'] in ['FORM_OPEN', 'SHOW_WINNERS_AUTOMATIC']:
                    # Boolean configs
                    current_value = config['value'].lower() == 'true'
                    new_value = st.checkbox("", value=current_value, key=key)
                    new_value_str = str(new_value)
                elif 'DATETIME' in config['key']:
                    # Datetime configs
                    try:
                        from datetime import datetime
                        current_dt = datetime.fromisoformat(config['value'].replace('Z', '+00:00'))
                        new_dt = st.datetime_input("", value=current_dt, key=key)
                        new_value_str = new_dt.strftime('%Y-%m-%d %H:%M:%S')
                    except:
                        new_value_str = st.text_input("", value=config['value'], key=key)
                elif config['key'] == 'WINNERS_TOP_N':
                    # Number config
                    current_num = int(config['value']) if config['value'].isdigit() else 1
                    new_num = st.number_input("", min_value=1, max_value=10, value=current_num, key=key)
                    new_value_str = str(new_num)
                else:
                    # Text configs
                    new_value_str = st.text_input("", value=config['value'], key=key)

                # Update button
                if st.button("💾", key=f"save_{config['key']}", help="Save"):
                    if db_service.update_configuration(config['key'], new_value_str):
                        st.success("✅ Updated!")
                        st.rerun()
                    else:
                        st.error("❌ Failed to update")

    with tabs[1]:  # Display Settings
        st.markdown("**Display Configuration**")

        display_configs = config_df[config_df['key'].isin([
            'SHOW_NILAI_CHIP', 'SHOW_AUTHOR', 'DEFAULT_TEXT_VIEW',
            'RUBRIK_INPUT_STYLE', 'SLIDER_LAYOUT', 'REQUIRE_CONFIRM_PANEL',
            'WINNER_DISPLAY_LAYOUT', 'SHOW_PDF_DOCUMENTS', 'SHOW_WINNER_SCORES', 'SHOW_ALL_SONGS_SCORES'
        ])]

        for _, config in display_configs.iterrows():
            col1, col2 = st.columns([1, 2])

            with col1:
                st.text(config['key'])
                if config.get('description'):
                    st.caption(config['description'])

            with col2:
                key = f"config_{config['key']}"

                if config['key'] in ['SHOW_NILAI_CHIP', 'SHOW_AUTHOR', 'REQUIRE_CONFIRM_PANEL', 'SHOW_PDF_DOCUMENTS', 'SHOW_WINNER_SCORES', 'SHOW_ALL_SONGS_SCORES']:
                    # Boolean configs
                    current_value = config['value'].lower() == 'true'
                    new_value = st.checkbox("", value=current_value, key=key)
                    new_value_str = str(new_value)
                elif config['key'] == 'RUBRIK_INPUT_STYLE':
                    # Dropdown config
                    options = ['dropdown', 'slider', 'radio']
                    current_idx = options.index(config['value']) if config['value'] in options else 0
                    new_value_str = st.selectbox("", options=options, index=current_idx, key=key)
                elif config['key'] == 'DEFAULT_TEXT_VIEW':
                    # Dropdown config
                    options = ['auto', 'full', 'compact']
                    current_idx = options.index(config['value']) if config['value'] in options else 0
                    new_value_str = st.selectbox("", options=options, index=current_idx, key=key)
                elif config['key'] == 'SLIDER_LAYOUT':
                    # Dropdown config
                    options = ['stacked', 'horizontal', 'compact']
                    current_idx = options.index(config['value']) if config['value'] in options else 0
                    new_value_str = st.selectbox("", options=options, index=current_idx, key=key)
                elif config['key'] == 'WINNER_DISPLAY_LAYOUT':
                    # Dropdown config for winner layout
                    options = ['TABS', 'COLUMNS']
                    current_idx = options.index(config['value']) if config['value'] in options else 0
                    new_value_str = st.selectbox("", options=options, index=current_idx, key=key)
                    st.caption("TABS: Current tabbed layout | COLUMNS: Side-by-side with full score")
                else:
                    # Text configs
                    new_value_str = st.text_input("", value=config['value'], key=key)

                # Update button
                if st.button("💾", key=f"save_{config['key']}", help="Save"):
                    if db_service.update_configuration(config['key'], new_value_str):
                        st.success("✅ Updated!")
                        st.rerun()
                    else:
                        st.error("❌ Failed to update")

    with tabs[2]:  # System Settings
        st.markdown("**System Configuration**")

        # Define system configuration keys
        system_keys = [
            'CERTIFICATE_MODE', 'CERTIFICATE_BUCKET', 'CERTIFICATE_FOLDER',
            'LOCK_FINAL_EVALUATIONS', 'DETECT_CHORDS_FALLBACK'
        ]

        system_configs = config_df[config_df['key'].isin(system_keys)]

        for _, config in system_configs.iterrows():
            col1, col2 = st.columns([1, 2])

            with col1:
                st.text(config['key'])
                if config.get('description'):
                    st.caption(config['description'])

            with col2:
                key = f"config_{config['key']}"

                if config['key'] in ['LOCK_FINAL_EVALUATIONS', 'DETECT_CHORDS_FALLBACK']:
                    # Boolean configs
                    current_value = config['value'].lower() == 'true'
                    new_value = st.checkbox("", value=current_value, key=key)
                    new_value_str = str(new_value)
                elif config['key'] == 'CERTIFICATE_MODE':
                    # Dropdown config
                    options = ['STORAGE', 'GENERATE']
                    current_idx = options.index(config['value']) if config['value'] in options else 0
                    new_value_str = st.selectbox("", options=options, index=current_idx, key=key)
                    st.caption("STORAGE: Use pre-generated certificates | GENERATE: Generate on-the-fly")
                else:
                    # Text configs
                    new_value_str = st.text_input("", value=config['value'], key=key)

                # Update button
                if st.button("💾", key=f"save_{config['key']}", help="Save"):
                    if db_service.update_configuration(config['key'], new_value_str):
                        st.success("✅ Updated!")
                        st.rerun()
                    else:
                        st.error("❌ Failed to update")

    with tabs[3]:  # Certificate Settings
        st.markdown("**Certificate Configuration**")

        # Certificate participant configs
        cert_participant_configs = config_df[config_df['key'].isin([
            'CERTIFICATE_LIST_MODE', 'CERTIFICATE_PARTICIPANTS', 'CERTIFICATE_PARTICIPANT_MAPPING'
        ])]

        for _, config in cert_participant_configs.iterrows():
            col1, col2 = st.columns([1, 2])

            with col1:
                st.text(config['key'])
                if config['key'] == 'CERTIFICATE_LIST_MODE':
                    st.caption("PARTICIPANT: Use participant names | SONG: Use song titles")
                elif config['key'] == 'CERTIFICATE_PARTICIPANTS':
                    st.caption("Comma-separated list of participant names")
                elif config['key'] == 'CERTIFICATE_PARTICIPANT_MAPPING':
                    st.caption("JSON mapping: participant name → certificate file")

            with col2:
                key = f"config_{config['key']}"

                if config['key'] == 'CERTIFICATE_LIST_MODE':
                    # Dropdown config
                    options = ['PARTICIPANT', 'SONG']
                    current_idx = options.index(config['value']) if config['value'] in options else 0
                    new_value_str = st.selectbox("", options=options, index=current_idx, key=key)
                elif config['key'] == 'CERTIFICATE_PARTICIPANTS':
                    # Text area for comma-separated list
                    new_value_str = st.text_area("", value=config['value'], height=100, key=key)
                elif config['key'] == 'CERTIFICATE_PARTICIPANT_MAPPING':
                    # Text area for JSON mapping
                    new_value_str = st.text_area("", value=config['value'], height=150, key=key)
                else:
                    # Text configs
                    new_value_str = st.text_input("", value=config['value'], key=key)

                # Update button
                if st.button("💾", key=f"save_{config['key']}", help="Save"):
                    if db_service.update_configuration(config['key'], new_value_str):
                        st.success("✅ Updated!")
                        st.rerun()
                    else:
                        st.error("❌ Failed to update")

        # Certificate template configs
        st.markdown("**Certificate Template Configuration**")
        cert_template_configs = config_df[config_df['key'].isin([
            'CERT_TEMPLATE_PARTICIPANT', 'CERT_TEMPLATE_WINNER', 'CERT_TEXT_COLOR_HEX'
        ])]

        for _, config in cert_template_configs.iterrows():
            col1, col2 = st.columns([1, 2])

            with col1:
                st.text(config['key'])
                if config['key'] == 'CERT_TEXT_COLOR_HEX':
                    st.caption("Hex color code for certificate text")

            with col2:
                key = f"config_{config['key']}"

                if config['key'] == 'CERT_TEXT_COLOR_HEX':
                    # Color picker
                    try:
                        current_color = config['value'] if config['value'].startswith('#') else '#000000'
                        new_color = st.color_picker("", value=current_color, key=key)
                        new_value_str = new_color
                    except:
                        new_value_str = st.text_input("", value=config['value'], key=key)
                else:
                    # Text area for templates
                    new_value_str = st.text_area("", value=config['value'], height=100, key=key)

                # Update button
                if st.button("💾", key=f"save_{config['key']}", help="Save"):
                    if db_service.update_configuration(config['key'], new_value_str):
                        st.success("✅ Updated!")
                        st.rerun()
                    else:
                        st.error("❌ Failed to update")

    with tabs[4]:  # Advanced Settings
        st.markdown("**Advanced Configuration**")

        # Scoring priority configs
        st.markdown("**Scoring Priority Settings**")
        scoring_configs = config_df[config_df['key'].isin([
            'CHORD_SOURCE_PRIORITY', 'DISPLAY_TEXT_PRIORITY', 'LYRICS_SCORE_PRIORITY', 'THEME_SCORE_PRIORITY'
        ])]

        for _, config in scoring_configs.iterrows():
            col1, col2 = st.columns([1, 2])

            with col1:
                st.text(config['key'])
                st.caption("Priority order for scoring algorithms")

            with col2:
                key = f"config_{config['key']}"
                new_value_str = st.text_area("", value=config['value'], height=80, key=key)

                # Update button
                if st.button("💾", key=f"save_{config['key']}", help="Save"):
                    if db_service.update_configuration(config['key'], new_value_str):
                        st.success("✅ Updated!")
                        st.rerun()
                    else:
                        st.error("❌ Failed to update")

        # Harmony weight configs
        st.markdown("**Harmony Analysis Weights**")
        harmony_configs = config_df[config_df['key'].isin([
            'HARM_W_EXT', 'HARM_W_NONDI', 'HARM_W_SLASH', 'HARM_W_TRANS', 'HARM_W_UNIQ'
        ])]

        for _, config in harmony_configs.iterrows():
            col1, col2 = st.columns([1, 2])

            with col1:
                st.text(config['key'])
                st.caption("Weight for harmony analysis")

            with col2:
                key = f"config_{config['key']}"
                current_num = int(config['value']) if config['value'].isdigit() else 0
                new_num = st.number_input("", min_value=0, max_value=100, value=current_num, key=key)
                new_value_str = str(new_num)

                # Update button
                if st.button("💾", key=f"save_{config['key']}", help="Save"):
                    if db_service.update_configuration(config['key'], new_value_str):
                        st.success("✅ Updated!")
                        st.rerun()
                    else:
                        st.error("❌ Failed to update")

        # System integration configs
        st.markdown("**System Integration**")
        integration_configs = config_df[config_df['key'].isin([
            'DRIVE_FOLDER_ROOT_ID'
        ])]

        for _, config in integration_configs.iterrows():
            col1, col2 = st.columns([1, 2])

            with col1:
                st.text(config['key'])
                st.caption("Google Drive folder ID for file storage")

            with col2:
                key = f"config_{config['key']}"
                new_value_str = st.text_input("", value=config['value'], key=key)

                # Update button
                if st.button("💾", key=f"save_{config['key']}", help="Save"):
                    if db_service.update_configuration(config['key'], new_value_str):
                        st.success("✅ Updated!")
                        st.rerun()
                    else:
                        st.error("❌ Failed to update")

        # Show other system configs that don't fit the main categories
        # Get all configs that are already handled in other tabs
        handled_configs = {
            # Contest Settings
            'THEME', 'FORM_OPEN', 'SUBMISSION_START_DATETIME', 'SUBMISSION_END_DATETIME',
            'FORM_OPEN_DATETIME', 'FORM_CLOSE_DATETIME', 'WINNER_ANNOUNCE_DATETIME',
            'WINNERS_TOP_N', 'SHOW_WINNERS_AUTOMATIC', 'TIMEZONE',
            # Display Settings
            'SHOW_NILAI_CHIP', 'SHOW_AUTHOR', 'DEFAULT_TEXT_VIEW',
            'RUBRIK_INPUT_STYLE', 'SLIDER_LAYOUT', 'REQUIRE_CONFIRM_PANEL',
            'WINNER_DISPLAY_LAYOUT', 'SHOW_PDF_DOCUMENTS', 'SHOW_WINNER_SCORES', 'SHOW_ALL_SONGS_SCORES',
            # System Settings
            'CERTIFICATE_MODE', 'CERTIFICATE_BUCKET', 'CERTIFICATE_FOLDER',
            'LOCK_FINAL_EVALUATIONS', 'DETECT_CHORDS_FALLBACK',
            # Certificate Settings
            'CERTIFICATE_LIST_MODE', 'CERTIFICATE_PARTICIPANTS', 'CERTIFICATE_PARTICIPANT_MAPPING',
            'CERT_TEMPLATE_PARTICIPANT', 'CERT_TEMPLATE_WINNER', 'CERT_TEXT_COLOR_HEX',
            # Advanced Settings
            'CHORD_SOURCE_PRIORITY', 'DISPLAY_TEXT_PRIORITY', 'LYRICS_SCORE_PRIORITY', 'THEME_SCORE_PRIORITY',
            'HARM_W_EXT', 'HARM_W_NONDI', 'HARM_W_SLASH', 'HARM_W_TRANS', 'HARM_W_UNIQ',
            'DRIVE_FOLDER_ROOT_ID'
        }

        other_configs = config_df[~config_df['key'].isin(handled_configs)]

        if not other_configs.empty:
            st.markdown("**Other System Configurations**")
            for _, config in other_configs.iterrows():
                col1, col2 = st.columns([1, 2])

                with col1:
                    st.text(config['key'])
                    if config.get('description'):
                        st.caption(config['description'])

                with col2:
                    key = f"config_{config['key']}"

                    if config['key'].startswith('HARM_W_'):
                        # Number configs for harmony weights
                        current_num = int(config['value']) if config['value'].isdigit() else 0
                        new_num = st.number_input("", min_value=0, max_value=100, value=current_num, key=key)
                        new_value_str = str(new_num)
                    else:
                        # Text configs
                        new_value_str = st.text_area("", value=config['value'], height=100, key=key)

                    # Update button
                    if st.button("💾", key=f"save_{config['key']}", help="Save"):
                        if db_service.update_configuration(config['key'], new_value_str):
                            st.success("✅ Updated!")
                            st.rerun()
                        else:
                            st.error("❌ Failed to update")

    with tabs[5]:  # Cleanup Tab
        render_configuration_cleanup_tab(config_df)

def should_include_config(config_key):
    """Filter out false positive configurations"""
    # Exclude Streamlit environment variables
    if config_key.startswith('STREAMLIT_'):
        return False

    # Exclude incomplete regex matches
    if config_key in ['HARM_W_', 'CERT_', 'SHOW_', 'FORM_']:
        return False

    # Exclude common false positives
    false_positives = {
        'HTTP_STATUS', 'ERROR_CODE', 'SUCCESS_CODE', 'DEBUG_MODE',
        'TEST_MODE', 'DEV_MODE', 'PROD_MODE', 'LOCAL_MODE'
    }
    if config_key in false_positives:
        return False

    return True

def scan_codebase_for_config_usage():
    """Scan codebase to find which configurations are actually used"""
    import os
    import re

    # Files to scan
    scan_paths = [
        'app.py',
        'components/',
        'services/',
        'sql/'
    ]

    used_configs = set()
    config_usage = {}  # config_key -> list of (file, line_number, context)

    def scan_file(file_path):
        """Scan a single file for config usage"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            for line_num, line in enumerate(lines, 1):
                # Look for config.get('KEY') or config['KEY'] patterns
                config_patterns = [
                    r"config\.get\(['\"]([A-Z_]+)['\"]",
                    r"config\[['\"]([A-Z_]+)['\"]\]",
                    r"['\"]([A-Z_][A-Z_]+)['\"]",  # Any uppercase string that looks like config
                ]

                for pattern in config_patterns:
                    matches = re.findall(pattern, line)
                    for match in matches:
                        # Filter to likely config keys (uppercase, underscores)
                        if len(match) > 3 and match.isupper() and '_' in match:
                            # Filter out false positives
                            if should_include_config(match):
                                used_configs.add(match)
                                if match not in config_usage:
                                    config_usage[match] = []
                                config_usage[match].append((file_path, line_num, line.strip()))

        except Exception as e:
            pass  # Skip files that can't be read

    # Scan all files
    for path in scan_paths:
        if os.path.isfile(path):
            scan_file(path)
        elif os.path.isdir(path):
            for root, dirs, files in os.walk(path):
                for file in files:
                    if file.endswith('.py'):
                        scan_file(os.path.join(root, file))

    return used_configs, config_usage

def render_configuration_cleanup_tab(config_df):
    """Render configuration cleanup tab with intelligent scanning"""
    st.markdown("**🧹 Configuration Cleanup**")

    # Add scan button
    col1, col2 = st.columns([1, 1])

    with col1:
        if st.button("🔍 Scan Codebase", help="Scan all Python files to detect which configs are actually used"):
            # Scan codebase for actual usage
            with st.spinner("🔍 Scanning codebase for configuration usage..."):
                used_configs, config_usage = scan_codebase_for_config_usage()

            # Store results in session state
            st.session_state.scan_results = {
                'used_configs': used_configs,
                'config_usage': config_usage
            }
            st.success(f"✅ Scanned codebase and found {len(used_configs)} configurations in use")

    with col2:
        use_manual_list = st.checkbox("📝 Use Manual List", value=True,
                                     help="Use manually curated list instead of automatic scan")

    # Determine which configs to consider as "expected"
    if use_manual_list or 'scan_results' not in st.session_state:
        # Manual curated list (current approach)
        expected_configs = {
            # Contest Settings
            'THEME', 'FORM_OPEN', 'SUBMISSION_START_DATETIME', 'SUBMISSION_END_DATETIME',
            'FORM_OPEN_DATETIME', 'FORM_CLOSE_DATETIME', 'WINNER_ANNOUNCE_DATETIME',
            'WINNERS_TOP_N', 'SHOW_WINNERS_AUTOMATIC', 'TIMEZONE',

            # Display Settings
            'SHOW_NILAI_CHIP', 'SHOW_AUTHOR', 'DEFAULT_TEXT_VIEW',
            'RUBRIK_INPUT_STYLE', 'SLIDER_LAYOUT', 'REQUIRE_CONFIRM_PANEL',
            'WINNER_DISPLAY_LAYOUT', 'SHOW_PDF_DOCUMENTS', 'SHOW_WINNER_SCORES', 'SHOW_ALL_SONGS_SCORES',

            # System Settings
            'CERTIFICATE_MODE', 'CERTIFICATE_BUCKET', 'CERTIFICATE_FOLDER',
            'LOCK_FINAL_EVALUATIONS', 'DETECT_CHORDS_FALLBACK',

            # Certificate Settings
            'CERTIFICATE_LIST_MODE', 'CERTIFICATE_PARTICIPANTS', 'CERTIFICATE_PARTICIPANT_MAPPING',
            'CERT_TEMPLATE_PARTICIPANT', 'CERT_TEMPLATE_WINNER', 'CERT_TEXT_COLOR_HEX',

            # Scoring & Analysis Settings
            'CHORD_SOURCE_PRIORITY', 'DISPLAY_TEXT_PRIORITY', 'LYRICS_SCORE_PRIORITY', 'THEME_SCORE_PRIORITY',
            'HARM_W_EXT', 'HARM_W_NONDI', 'HARM_W_SLASH', 'HARM_W_TRANS', 'HARM_W_UNIQ',

            # System Integration
            'DRIVE_FOLDER_ROOT_ID'
        }
        st.info("📝 Using manually curated configuration list")
    else:
        # Use scan results
        scan_data = st.session_state.scan_results
        used_configs = scan_data['used_configs']
        config_usage = scan_data['config_usage']

        # Essential configs that should always be kept (even if not detected in scan)
        essential_configs = {
            'THEME', 'FORM_OPEN', 'TIMEZONE', 'CERTIFICATE_MODE', 'CERTIFICATE_BUCKET'
        }

        expected_configs = used_configs | essential_configs
        st.success(f"🔍 Using scan results: {len(expected_configs)} configurations detected")

        # Show scan details
        with st.expander("📊 Scan Results Details"):
            for config in sorted(expected_configs):
                if config in config_usage:
                    usage_count = len(config_usage[config])
                    st.text(f"• {config} (found in {usage_count} places)")

                    # Show first few usages
                    if st.checkbox(f"Show details for {config}", key=f"details_{config}"):
                        for file_path, line_num, context in config_usage[config][:3]:
                            st.code(f"{file_path}:{line_num} - {context}")
                        if len(config_usage[config]) > 3:
                            st.caption(f"... and {len(config_usage[config]) - 3} more")
                else:
                    st.text(f"• {config} (essential config)")

    st.markdown("---")

    # Find unused configurations
    current_keys = set(config_df['key'].tolist())
    unused_configs = current_keys - expected_configs
    missing_configs = expected_configs - current_keys

    # Safety warning
    if unused_configs:
        st.warning("⚠️ **PERINGATAN**: Konfigurasi di bawah mungkin masih digunakan di bagian lain aplikasi. Jangan hapus tanpa verifikasi!")
        st.info("💡 **Tips**: Cek kode aplikasi terlebih dahulu sebelum menghapus konfigurasi apapun.")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**❌ Unused Configurations**")
        if unused_configs:
            st.warning(f"Found {len(unused_configs)} unused configurations:")
            for key in sorted(unused_configs):
                st.text(f"• {key}")

            st.error("🚨 **DANGER ZONE** - Penghapusan konfigurasi dapat merusak aplikasi!")

            # Require confirmation
            confirm_delete = st.checkbox("☑️ Saya yakin ingin menghapus konfigurasi ini", key="confirm_delete_unused")

            if confirm_delete and st.button("🗑️ Remove All Unused", key="remove_unused", help="Remove all unused configurations"):
                from services.database_service import db_service
                removed_count = 0
                for key in unused_configs:
                    # Note: You'll need to implement delete_config method in database_service
                    st.write(f"⚠️ Would remove: {key}")
                    removed_count += 1
                st.warning(f"⚠️ Would remove {removed_count} configurations - FEATURE DISABLED FOR SAFETY")
                st.info("💡 Manual verification required before implementing delete functionality")
        else:
            st.success("✅ No unused configurations found")

    with col2:
        st.markdown("**➕ Missing Configurations**")
        if missing_configs:
            st.info(f"Found {len(missing_configs)} missing configurations:")
            for key in sorted(missing_configs):
                st.text(f"• {key}")

            if st.button("➕ Add Missing Configs", key="add_missing", help="Add missing configurations with defaults"):
                from services.database_service import db_service
                # Default values for missing configs
                defaults = {
                    # Contest Settings
                    'THEME': 'LOMBA CIPTA LAGU THEME SONG BULAN KELUARGA GKI PERUMNAS 2025',
                    'FORM_OPEN': 'True',
                    'SUBMISSION_START_DATETIME': '2025-08-01 00:00:00',
                    'SUBMISSION_END_DATETIME': '2025-08-31 23:59:59',
                    'FORM_OPEN_DATETIME': '2025-09-01 00:00:00',
                    'FORM_CLOSE_DATETIME': '2025-09-30 23:59:59',
                    'WINNER_ANNOUNCE_DATETIME': '2025-10-15 00:00:00',
                    'WINNERS_TOP_N': '3',
                    'SHOW_WINNERS_AUTOMATIC': 'False',
                    'TIMEZONE': 'Asia/Jakarta',

                    # Display Settings
                    'SHOW_NILAI_CHIP': 'True',
                    'SHOW_AUTHOR': 'True',
                    'DEFAULT_TEXT_VIEW': 'auto',
                    'RUBRIK_INPUT_STYLE': 'dropdown',
                    'SLIDER_LAYOUT': 'stacked',
                    'REQUIRE_CONFIRM_PANEL': 'True',
                    'WINNER_DISPLAY_LAYOUT': 'COLUMNS',
                    'SHOW_PDF_DOCUMENTS': 'False',
                    'SHOW_WINNER_SCORES': 'True',
                    'SHOW_ALL_SONGS_SCORES': 'False',

                    # System Settings
                    'CERTIFICATE_MODE': 'STORAGE',
                    'CERTIFICATE_BUCKET': 'song-contest-files',
                    'CERTIFICATE_FOLDER': 'certificates',
                    'LOCK_FINAL_EVALUATIONS': 'True',
                    'DETECT_CHORDS_FALLBACK': 'True',

                    # Certificate Settings
                    'CERTIFICATE_LIST_MODE': 'PARTICIPANT',
                    'CERTIFICATE_PARTICIPANTS': '',
                    'CERTIFICATE_PARTICIPANT_MAPPING': '{}',
                    'CERT_TEMPLATE_PARTICIPANT': '',
                    'CERT_TEMPLATE_WINNER': '',
                    'CERT_TEXT_COLOR_HEX': '#000000',

                    # Advanced Settings
                    'CHORD_SOURCE_PRIORITY': '',
                    'DISPLAY_TEXT_PRIORITY': '',
                    'LYRICS_SCORE_PRIORITY': '',
                    'THEME_SCORE_PRIORITY': '',
                    'HARM_W_EXT': '10',
                    'HARM_W_NONDI': '10',
                    'HARM_W_SLASH': '10',
                    'HARM_W_TRANS': '10',
                    'HARM_W_UNIQ': '10',
                    'DRIVE_FOLDER_ROOT_ID': ''
                }

                added_count = 0
                for key in missing_configs:
                    default_value = defaults.get(key, 'True')
                    if db_service.update_config(key, default_value):
                        st.write(f"✅ Added: {key} = {default_value}")
                        added_count += 1
                    else:
                        st.write(f"❌ Failed to add: {key}")

                if added_count > 0:
                    cache_service.invalidate_cache()
                    st.success(f"Added {added_count} missing configurations!")
                    st.rerun()
        else:
            st.success("✅ All expected configurations exist")

def export_all_data():
    """Export all evaluation data"""
    try:
        # Get all data
        evaluations_df = cache_service.get_cached_evaluations()
        judges_df = cache_service.get_cached_judges()
        songs_df = cache_service.get_cached_songs()

        if not evaluations_df.empty:
            # Create comprehensive export
            export_data = evaluations_df.merge(
                judges_df[['id', 'name']].rename(columns={'name': 'judge_name'}),
                left_on='judge_id', right_on='id', how='left'
            ).merge(
                songs_df[['id', 'title']].rename(columns={'title': 'song_title'}),
                left_on='song_id', right_on='id', how='left'
            )

            # Convert to CSV
            csv = export_data.to_csv(index=False)

            st.download_button(
                label="📥 Download CSV",
                data=csv,
                file_name=f"lomba_evaluations_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
            st.success("Export ready for download!")
        else:
            st.warning("No data to export")
    except Exception as e:
        st.error(f"Export failed: {e}")
