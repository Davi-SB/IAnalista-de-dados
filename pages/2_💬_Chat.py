import openai
import pandas as pd
from dotenv import load_dotenv, find_dotenv
import streamlit as st
import time
from io import BytesIO  # Importa BytesIO para trabalhar com a imagem em memória

# Carrega variáveis de ambiente e configura o cliente OpenAI (ajuste conforme necessário)
#load_dotenv(find_dotenv())
#client = openai.Client()

# Configuração da página
st.set_page_config(
    page_title="IAnalista - Chat",  # título da aba
    layout="wide",              # layout centralizado
    page_icon=":bar_chart:"         # ícone da aba
)

# Verifica se a chave foi fornecida, se sim, configura o cliente
if st.session_state.api_key:
    client = openai.Client(api_key=st.session_state.api_key)
else:
    st.sidebar.warning("Por favor, insira sua chave da API OpenAI para prosseguir.")
    st.switch_page("1_🏡_Home.py")
    

# Botão na sidebar para limpar todo o session_state
if st.sidebar.button("Limpar sessão", use_container_width=True):
    st.session_state.clear()

st.sidebar.link_button("Feito por Davi Brilhante", "https://github.com/Davi-SB/", type='tertiary')

# Inicializa o histórico na session_state se ainda não existirem
if "messages" not in st.session_state: 
    st.session_state.messages = []
if "dataset" not in st.session_state: 
    st.session_state.dataset = None
if "file" not in st.session_state: 
    st.session_state.file = None
if "DataAssistant" not in st.session_state: 
    st.session_state.DataAssistant = None
if "myThread" not in st.session_state: 
    st.session_state.myThread = None
if "run" not in st.session_state: 
    st.session_state.run = None
if "run_steps" not in st.session_state: 
    st.session_state.run_steps = None

# Renderiza as mensagens já armazenadas no histórico (se houver)
for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.chat_message("user").markdown(msg["content"])
        # Se a mensagem indicar upload do CSV, exibe o dataset também.
        if ('CSV enviado: ' in msg['content']) and (st.session_state.dataset is not None):
            st.write(st.session_state.dataset)
    else:
        # Se for uma mensagem de imagem, exibe a imagem. Caso contrário, renderiza como texto.
        if msg.get("type") == "image":
            st.chat_message("assistant").image(msg["content"])
        else:
            st.chat_message("assistant").markdown(msg["content"])

# UPLOAD DO DATASET
if st.session_state.dataset is None:
    st.header("Envie seu dataset (CSV)")
    uploaded_file = st.file_uploader("Selecione um arquivo CSV", type="csv")
    
    if uploaded_file is None:
        st.markdown("#")
        st.caption("Quer um dataset para testar? Escolha um dos exemplos disponíveis para enviar para seu agente!")
        col1 , col2 = st.columns(2)
        button_netflix = col1.button("Dataset com o catálogo da Netflizx", use_container_width=True)
        button_spotify = col2.button("Dataset com músicas do Spotify", use_container_width=True)
        if button_netflix:
            try:
                with open("full_netflix_dataset.csv", "rb") as f:
                    data = f.read()
                # Cria um objeto BytesIO e define o atributo name
                uploaded_file = BytesIO(data)
                uploaded_file.name = "full_netflix_dataset.csv"
                st.success("Dataset do catálogo da Netflix carregado com sucesso!")
            except Exception as e:
                st.error(f"Erro ao carregar o dataset: {e}")
        if button_spotify:
            try:
                with open("spotify_dataset.csv", "rb") as f:
                    data = f.read()
                uploaded_file = BytesIO(data)
                uploaded_file.name = "spotify_dataset.csv"
                st.success("Dataset do Spotify carregado com sucesso!")
            except Exception as e:
                st.error(f"Erro ao carregar o dataset: {e}")
                time.sleep(5)
                st.rerun()
            
    if uploaded_file is not None:
        try:
            # Lê o CSV com pandas e salva no session_state
            df = pd.read_csv(uploaded_file)
            st.session_state.dataset = df

            # Atualiza o histórico com uma notificação de recebimento do CSV
            msg = f"CSV enviado: {uploaded_file.name}"
            st.session_state.messages.append({"role": "user", "content": msg})
            st.chat_message("user").markdown(msg)
            
            # Exibe o dataset
            st.write(df)
            
            # Salva o arquivo para a criação do agente
            st.session_state.file = client.files.create(
                file=uploaded_file.getvalue(),  # lê os bytes do arquivo
                purpose='assistants'
            )
        
            if st.session_state.DataAssistant is None:
                with st.spinner("Criando um agente especialista no seu dataset... 🤖"):
                    st.session_state.DataAssistant = client.beta.assistants.create(
                        name="AInalista de Dados",
                        instructions=('Você é um Engenheiro de Dados. Você recebeu um arquivo .CSV, um dataset com informações importantes. '
                                    'Sua tarefa é analisar o arquivo e responder as perguntas sobre os dados e desenvolver códigos quando necessário.'),
                        tools=[{'type': 'code_interpreter'}],
                        tool_resources={'code_interpreter': {'file_ids': [st.session_state.file.id]}},
                        model='gpt-4o-mini'
                    )
                if st.session_state.myThread is None:
                    st.session_state.myThread = client.beta.threads.create()
            st.success("Agente criado com sucesso!")
            
            # Exibe a resposta do assistente com streaming
            resposta_completa = "Arquivo CSV recebido com sucesso! Estou pronto para receber perguntas sobre o dataset."
            mensagem_parcial = ""
            mensagem_assistente = st.chat_message("assistant")
            with mensagem_assistente:
                placeholder = st.empty()
                for caractere in resposta_completa:
                    mensagem_parcial += caractere
                    placeholder.markdown(mensagem_parcial)
                    time.sleep(0.01)
            st.session_state.messages.append({"role": "assistant", "content": resposta_completa})
            st.rerun()
        except Exception as e:
            st.error("Certifique-se que sua API KEY está correta e tente novamente.")
            st.error(f"Erro ao ler o CSV: {e}")
            time.sleep(5)
            st.rerun()

# CHAT PARA PERGUNTAS
if st.session_state.dataset is not None:
    prompt = st.chat_input("Faça sua pergunta sobre o dataset")
    
    if prompt:
        # Registra e exibe a mensagem do usuário
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.chat_message("user").markdown(prompt)
        
        message = client.beta.threads.messages.create(  # cria uma mensagem
            thread_id=st.session_state.myThread.id,        # na thread especificada
            role='user',
            content=prompt
        )
        
        st.session_state.run = client.beta.threads.runs.create(
            thread_id=st.session_state.myThread.id,
            assistant_id=st.session_state.DataAssistant.id,
            instructions='O usuário fará perguntas sobre um dataset.'
        )
        
        with st.spinner("Pensando... 🤔"):
            while st.session_state.run.status in ['queued', 'in_progress', 'cancelling']:
                st.session_state.run = client.beta.threads.runs.retrieve(
                    thread_id=st.session_state.myThread.id,  
                    run_id=st.session_state.run.id           
                )
        st.success("Pronto!")
        
        st.session_state.run_steps = client.beta.threads.runs.steps.list(
            thread_id=st.session_state.myThread.id,
            run_id=st.session_state.run.id
        )
        
        # Processa os steps em ordem reversa
        for step in st.session_state.run_steps.data[::-1]:
            if step.step_details.type == 'tool_calls':
                for tool_call in step.step_details.tool_calls:
                    codigo = tool_call.code_interpreter.input
                    conteudo_code_block = f"```\n{codigo}\n```"
                    
                    # Streaming para tool_calls
                    mensagem_parcial = ""
                    mensagem_assistente = st.chat_message("assistant")
                    with mensagem_assistente:
                        placeholder = st.empty()
                        for caractere in conteudo_code_block:
                            mensagem_parcial += caractere
                            placeholder.markdown(mensagem_parcial)
                            time.sleep(0.01)
                    
                    st.session_state.messages.append({"role": "assistant", "content": conteudo_code_block})
            
            elif step.step_details.type == 'message_creation':
                message_resp = client.beta.threads.messages.retrieve(
                    thread_id=st.session_state.myThread.id,
                    message_id=step.step_details.message_creation.message_id
                )
                conteudo = message_resp.content[0]
                
                # Se for texto, aplicamos streaming caractere por caractere.
                if conteudo.type == 'text':
                    texto_mensagem = conteudo.text.value
                    mensagem_parcial = ""
                    mensagem_assistente = st.chat_message("assistant")
                    with mensagem_assistente:
                        placeholder = st.empty()
                        for caractere in texto_mensagem:
                            mensagem_parcial += caractere
                            placeholder.markdown(mensagem_parcial)
                            time.sleep(0.01)
                    st.session_state.messages.append({"role": "assistant", "content": texto_mensagem})
                
                # Se for imagem, exibe a imagem diretamente sem salvá-la localmente.
                elif conteudo.type == 'image_file':
                    file_id = conteudo.image_file.file_id
                    image_data = client.files.content(file_id)
                    try:
                        # Lê os bytes da imagem em memória
                        image_bytes = image_data.read()
                        # Exibe a imagem no chat utilizando os bytes carregados
                        st.chat_message("assistant").image(image_bytes)
                        st.session_state.messages.append({"role": "assistant", "type": "image", "content": image_bytes})
                    except Exception as e:
                        st.error(f"Erro ao exibir a imagem: {e}")
