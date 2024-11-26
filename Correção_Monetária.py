# bash: streamlit run Correção_Monetária.py
import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_icon='img/iconw.png', page_title='PDDE Smart', layout='wide')

a,b = st.columns(2)
with a:
    st.image('img/logo-pdde-smart.png')

# Cache
@st.cache_data
def load_data():
    df = pd.read_pickle('data/ideges.pkl', compression='gzip')
    return df

df = load_data()
    
list_estado = df['estado'].sort_values().unique()
list_regiao = df['regiao'].sort_values().unique()
list_municipio = df['municipio'].sort_values().unique()
list_ano = df['ano_exercicio'].sort_values().unique()
list_escola = df['cod_escola'].sort_values().dropna().astype(int).unique()


with st.sidebar:
    st.image('img/cecampe.png')
    uano = st.multiselect('Ano Exercício', list_ano, None, placeholder='Todos')
    ureg = st.multiselect('Região', list_regiao, None, placeholder='Todos')
    uuf = st.multiselect('Estado', list_estado, None, placeholder='Todos')    
    umun = st.multiselect('Município', list_municipio, None, placeholder='Todos')
    uescola = st.multiselect('Escola', list_escola, None, placeholder='Todos')
        
print(uano)
if len(uano)!=0:
    df = df[df.ano_exercicio.isin(uano)]    
if len(ureg)!=0:
    df = df[df.regiao.isin(ureg)]   
if len(uuf)!=0:
    df = df[df.estado.isin(uuf)]
if len(umun)!=0:
    df = df[df.municipio.isin(umun)]  
if len(uescola)!=0:
    df = df[df.cod_escola.isin(uescola)]
    

st.markdown('## Correção Monetária')

with st.expander('Especificar Índice de Preço'):
    p = st.radio("Índice de Preço", ["IPCA", "IGP", "IGPM"])

with st.expander('Especificar Indicador Financeiro'):
    v = st.radio("Indicadores", ["total_recebido", "saldo_cc_final", "saldo_cc_inicial"])

df['valor_real'] = df[v]/df[p.lower()]
df_agg = (
    df.groupby(['ano_exercicio', 'regiao'])
    .agg({v:'sum',
          'valor_real':'sum'})
    .reset_index())
 
vn =  df_agg[v].sum().round(0)
vn = f'R$ {vn:,.0f}'

vr =  df['valor_real'].sum().round(0)
vr = f'R$ {vr:,.0f}'

with st.expander('Evolução', True):
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric('Total de escolas beneficiadas', len(list_escola))
    with col2:
        st.metric(f'{v.upper()} Nominal', vn.replace(',','.'))
    with col3:
        st.metric(f'{v.upper()} Real (dez.2023)', vr.replace(',','.'))
        
    col1, col2 = st.columns(2)

    df_agg = df_agg.astype({'ano_exercicio':int})
    with col1:
        fig1 = px.line(df_agg, x='ano_exercicio', y=v, color='regiao',
                    labels={'ano_exercicio':'Ano',v: 'Valor Nominal'},
                    title=f"Valor nominal do indicador {v}")
        st.plotly_chart(fig1, use_container_width=True)
        
    with col2:
        fig2 = px.line(df_agg, x='ano_exercicio', y='valor_real', color='regiao',
                    labels={'ano_exercicio':'Ano',v: 'Valor Real'},
                    title=f"Valor real do indicador {v}")
        st.plotly_chart(fig2, use_container_width=True)

    st.dataframe(df_agg.style.format(thousands='.', decimal=',', precision=0), 
                use_container_width=True, hide_index=True,
                column_config={
                    'ano_exercicio': st.column_config.TextColumn("Ano Exercício"),
                    'regiao': st.column_config.TextColumn("Região"),
                    v: st.column_config.NumberColumn(
                        "Faturamento Contábil", help=f"Indicador {v.upper()}"),
                    'valor_real': st.column_config.NumberColumn(
                        "Valor Real (dez.23)", help="Valor corrigido pela inflação")})