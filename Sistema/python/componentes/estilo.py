
import streamlit as st


def aplicar_estilo():

    st.markdown("""
    <style>

    :root {
        color-scheme: light;

        --tl-red: #8F302B;
        --tl-red-dark: #70231F;
        --tl-cream: #F5F2EA;
        --tl-white: #FFFFFF;
        --tl-text: #29352F;
        --tl-muted: #777D75;
        --tl-border: #E6DFD3;
        --tl-green: #315D49;
        --tl-gold: #C49A4A;
    }

    html, body {
        background-color: var(--tl-cream) !important;
        color: var(--tl-text) !important;
        color-scheme: light !important;
        font-family: "Inter", "Segoe UI", sans-serif;
    }

    [data-testid="stAppViewContainer"],
    [data-testid="stMain"] {
        background-color: var(--tl-cream) !important;
    }

    [data-testid="stHeader"] {
        background-color: transparent !important;
    }

    .block-container {
        padding-top: 2rem;
        padding-bottom: 3.5rem;
        max-width: 1500px;
    }

    h1, h2, h3, h4 {
        color: var(--tl-green) !important;
        font-family: "Inter", "Segoe UI", sans-serif;
        font-weight: 700 !important;
        letter-spacing: -0.5px;
    }

    h1 {
        font-size: 2.2rem !important;
    }

    h2 {
        font-size: 1.65rem !important;
    }

    h3 {
        font-size: 1.3rem !important;
    }

    p, label, li {
        color: var(--tl-text);
    }

    [data-testid="stCaptionContainer"] {
        color: var(--tl-muted);
    }

    [data-testid="stSidebar"],
    [data-testid="stSidebar"] > div:first-child {
        background-color: var(--tl-red) !important;
    }

    [data-testid="stSidebar"] {
        border-right: 1px solid var(--tl-red-dark);
    }

    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] span {
        color: #FFF8F0 !important;
    }

    [data-testid="stSidebarNav"] {
        padding-top: 1rem;
    }

    [data-testid="stSidebarNav"]::before {
        content: "🌮  TacoLoko";
        display: block;
        color: #FFFFFF;
        font-size: 1.55rem;
        font-weight: 800;
        letter-spacing: -0.7px;
        padding: 0.8rem 1rem 1.5rem;
        border-bottom: 1px solid rgba(255,255,255,0.18);
        margin-bottom: 1rem;
    }

    [data-testid="stSidebarNav"] a {
        border-radius: 10px;
        margin: 3px 7px;
        padding: 0.55rem 0.8rem;
        transition: background 0.2s ease;
    }

    [data-testid="stSidebarNav"] a:hover {
        background-color: rgba(255,255,255,0.13);
    }

    [data-testid="stSidebarNav"] a[aria-current="page"] {
        background-color: var(--tl-cream) !important;
        border-radius: 10px;
    }

    [data-testid="stSidebarNav"] a[aria-current="page"] span,
    [data-testid="stSidebarNav"] a[aria-current="page"] p {
        color: var(--tl-red) !important;
        font-weight: 700 !important;
    }

    [data-testid="stSidebarNav"] a[aria-current="page"] svg {
        color: var(--tl-red) !important;
        stroke: var(--tl-red) !important;
    }

    [data-testid="stMetric"] {
        background-color: var(--tl-white) !important;
        border: 1px solid var(--tl-border) !important;
        border-radius: 14px;
        padding: 18px 20px;
        box-shadow: 0 3px 12px rgba(35,48,39,0.04);
    }

    [data-testid="stMetricLabel"] p {
        color: var(--tl-muted) !important;
        font-weight: 500;
        font-size: 0.86rem;
    }

    [data-testid="stMetricValue"] {
        color: var(--tl-green) !important;
        font-weight: 750;
    }

    [data-testid="stButton"] button,
    [data-testid="stFormSubmitButton"] button {
        border-radius: 9px !important;
        font-weight: 650 !important;
        transition: all 0.2s ease;
        border: 1px solid var(--tl-border) !important;
        box-shadow: none !important;
    }

    [data-testid="stButton"] button[kind="primary"],
    [data-testid="stFormSubmitButton"] button[kind="primary"] {
        background-color: var(--tl-red) !important;
        color: white !important;
        border-color: var(--tl-red) !important;
    }

    [data-testid="stButton"] button[kind="primary"]:hover,
    [data-testid="stFormSubmitButton"] button[kind="primary"]:hover {
        background-color: var(--tl-red-dark) !important;
        border-color: var(--tl-red-dark) !important;
    }

    [data-testid="stButton"] button[kind="secondary"],
    [data-testid="stFormSubmitButton"] button[kind="secondary"] {
        background-color: white !important;
        color: var(--tl-red) !important;
        border-color: var(--tl-border) !important;
    }

    [data-testid="stTextInput"] input,
    [data-testid="stNumberInput"] input,
    [data-testid="stTextArea"] textarea {
        background-color: white !important;
        color: var(--tl-text) !important;
        border: 1px solid var(--tl-border) !important;
        border-radius: 8px !important;
        box-shadow: none !important;
    }

    [data-baseweb="input"],
    [data-baseweb="textarea"] {
        background-color: white !important;
        border-color: var(--tl-border) !important;
        box-shadow: none !important;
    }

    [data-baseweb="select"] > div {
        background-color: white !important;
        color: var(--tl-text) !important;
        border: 1px solid var(--tl-border) !important;
        border-radius: 8px !important;
        box-shadow: none !important;
    }

    [data-baseweb="select"] input {
        color: var(--tl-text) !important;
    }

    [data-testid="stTextInput"] input:focus,
    [data-testid="stNumberInput"] input:focus,
    [data-testid="stTextArea"] textarea:focus {
        border-color: var(--tl-red) !important;
        box-shadow: 0 0 0 1px var(--tl-red) !important;
    }

    [data-testid="stExpander"] {
        background-color: white !important;
        border: 1px solid var(--tl-border) !important;
        border-radius: 12px !important;
        overflow: hidden;
    }

    [data-testid="stExpander"] summary {
        color: var(--tl-green) !important;
        font-weight: 650;
    }

    [data-testid="stTabs"] button[role="tab"] {
        color: var(--tl-muted) !important;
        font-weight: 600;
    }

    [data-testid="stTabs"] button[role="tab"][aria-selected="true"] {
        color: var(--tl-red) !important;
        border-bottom-color: var(--tl-red) !important;
    }

    [data-testid="stAlert"] {
        background-color: #F8F1EF !important;
        border: 1px solid #E9D8D4 !important;
        border-left: 4px solid var(--tl-red) !important;
        border-radius: 10px !important;
        color: var(--tl-text) !important;
    }

    [data-testid="stAlert"] p {
        color: var(--tl-text) !important;
    }

    [data-testid="stDataFrame"],
    [data-testid="stTable"] {
        background-color: white !important;
        border: 1px solid var(--tl-border) !important;
        border-radius: 11px !important;
        overflow: hidden;
    }

    [data-testid="stFileUploader"] {
        background-color: white !important;
        border: 1px dashed #D6C9B6 !important;
        border-radius: 11px !important;
        padding: 0.5rem;
    }

    [data-testid="stImage"] img {
        border-radius: 12px;
    }

    [data-testid="stProgressBar"] > div > div {
        background-color: var(--tl-red) !important;
    }

    [data-testid="stCheckbox"] label {
        color: var(--tl-text) !important;
    }

    hr {
        border-color: var(--tl-border) !important;
    }

    ::selection {
        background-color: #EBC6B6;
        color: var(--tl-red);
    }

    @media (max-width: 768px) {
        .block-container {
            padding-top: 1.2rem;
            padding-left: 1rem;
            padding-right: 1rem;
        }

        h1 {
            font-size: 1.8rem !important;
        }
    }

    </style>
    """, unsafe_allow_html=True)
