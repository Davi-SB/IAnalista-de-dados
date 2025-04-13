import streamlit as st

st.set_page_config(
    page_title="IAnalista de Dados", # seta o título da aba
    layout="wide",                   # ocupa o espaço centralizado na tela
    page_icon=":bar_chart:",         # seta o ícone da aba
    initial_sidebar_state="expanded" # inicia a sidebar aberta
)

if 'api_key' not in st.session_state:
    st.session_state.api_key = None
    
if st.sidebar.button("Limpar sessão", use_container_width=True):
    st.session_state.clear()
st.sidebar.link_button("Feito por Davi Brilhante", "https://github.com/Davi-SB/", type='tertiary')

st.header("📊 IAnalista de Dados 📊")
st.divider()
st.markdown("#### **Seja bem-vindo ao *`IAnalista`*!**")
st.markdown("#### **Aqui você pode fazer perguntas sobre os `dados` e obter `respostas` em tempo real.**")
st.divider()

# Campo para inserção da API key
st.markdown("#### Insira sua **chave de API da OpenAI** para começar.")
st.caption("Atenção: este valor será armazenado apenas durante a sessão atual e não será salvo permanentemente.")
api_key = st.text_input(
    "Digite sua chave de API", 
    type="password",
    key="api_key_input"
)

# Armazenando a chave na session_state, se houver
if api_key:
    st.session_state.api_key = api_key
    st.success("Chave de API definida para esta sessão!")

if st.session_state.api_key is not None:
    for _ in range(4):
        st.write("")

    left, middle, right = st.columns(3)

    if middle.button("Clique aqui para começar!", use_container_width=True):
        # Opcional: você pode verificar se a API key foi inserida antes de mudar de página
        if "api_key" not in st.session_state or not st.session_state.api_key:
            st.warning("Por favor, insira sua chave de API antes de prosseguir.")
        else:
            st.switch_page("pages/2_💬_Chat.py")