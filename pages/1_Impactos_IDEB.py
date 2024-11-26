import streamlit as st
from pandas import read_pickle, read_html, concat
from sklearn import linear_model
import statsmodels.api as sm
from numpy import log, exp, abs, where
import plotly.express as px
from sklearn.metrics import (mean_squared_error, r2_score, mean_absolute_percentage_error,
                             root_mean_squared_error, mean_absolute_error)

st.set_page_config(page_icon='img/iconw.png', page_title='PDDE Smart', layout='wide')

a,b = st.columns(2)
with a:
    st.image('img/logo-pdde-smart.png')


with st.sidebar:
    st.image('img/cecampe.png')
    ulevel = st.selectbox('Nível de Ensino', ['5º ano - EF', '9º ano - EF'],
                          help='Séries avaliadas no SAEB')
    unorm = st.toggle('Dados normalizados', True,
                      help='''A normalização dos dados é aplicada aos atributos (variáveis explicativas) e
                      na variável dependente aplica-se o logaritmo neperiano.
                      ''')
    uloc = st.toggle('Localização da escola', True)
    uinfra = st.toggle('Infraestrutura da escola', True)
    uporte = st.toggle('Porte da escola', True)
    ufeuf = st.toggle('Efeito fixo estadual', True)
    

st.markdown(f'## Impactos IDEB: {ulevel}')

@st.cache_data
def load_data():
    df = read_pickle('data/ideb_pred.pkl', compression='gzip')
    return df

df = load_data()

uano = st.slider('Ano', min_value=2017, max_value=2021, value=2021, step=2)

atributos = ['PDDE', 'Escola Municipal']

if uloc:
    atributos = atributos + ['Zona Rural', 'Terra indígena',
                             'Área de assentamento', 'Área de quilombos']
        
if uinfra:
    atributos = atributos + ['Esgoto inexistente', 'Biblioteca', 'Laboratorio informatica',
                             'Quadra esportes', 'Banda larga']

if uporte:
    atributos = atributos + ['Matrículas: Até 50', 'Matrículas: 50 a 100',
                             'Matrículas: 100 a 200', 'Matrículas: 200 a 500',
                             'Matrículas: 500 a 1000', 'Matrículas: Mais de 1000']
if ufeuf:
    atributos = atributos + ['AC', 'AL', 'AM', 'AP', 'BA', 'CE', 'DF', 'ES',
                             'GO', 'MA', 'MG', 'MS', 'MT', 'PA', 'PB', 'PE', 
                             'PI', 'PR', 'RJ', 'RN', 'RO', 'RR', 'RS', 'SC', 
                             'SE', 'SP', 'TO']
    
nivel = {'5º ano - EF': 'ideb5', '9º ano - EF': 'ideb9', '3º ano - EM': 'ideb12'}                      
impacto = [nivel[ulevel]]
data = df[df.Ano==uano][['Escola']+atributos + impacto].dropna()

y = data[impacto]
x = data.drop(impacto+['Escola'],axis=1)
if unorm:
    x = (x - x.min())/(x.max() - x.min())
    y = log(data[impacto])

with st.expander(f'Amostra de dados {uano}', False):
    st.dataframe(concat([data[['Escola']].astype({'Escola':str}),y,x], axis=1))
    
lr = linear_model.LinearRegression()
lr.fit(x, y)
y_pred = lr.predict(x)
r2 = r2_score(y, y_pred)
mse = mean_squared_error(y, y_pred) 
rmse =root_mean_squared_error(y, y_pred)
mae = mean_absolute_error(y, y_pred) 
mape = mean_absolute_percentage_error(y, y_pred) 

ols = sm.OLS(y, x.assign(cons=1))
ols_result = ols.fit()
results_summary = ols_result.summary(slim=True)

results_as_html = results_summary.tables[1].as_html()
ols_df = read_html(results_as_html, header=0, index_col=0)[0].reset_index()
ols_df.columns = ['Variável','Coeficiente', 'Erro-Padrão', 't', 'P-valor', 'LI(95%)', 'LS(95%)']

delta = ols_df.query('Variável=="PDDE"')['Coeficiente'].iloc[0]
if unorm:
    delta = (exp(delta)-1)*100
    delta = f'{delta:.2f}%'
else:
    delta = f'{delta:.3f} pt'

with st.expander(f'Resultados do PDDE sobre o IDEB – {uano}', True):
    a,b,c = st.columns(3)
    with a:
        st.metric(f'Impacto Previsto', delta, help='Estimativa calculada a partir de um modelo linear')
    with b: 
        st.metric(f'Coeficiente de Determinação', f'{r2*100:.0f}%', 
                  help='Grau de determinação do ajustamento do modelo (R2)')
    with c: 
        st.metric(f'MAPE', f'{mape*100:.0f}%', help='Erro percentual absoluto médio')
        
    st.dataframe(ols_df[['Variável','Coeficiente', 'Erro-Padrão', 'P-valor']], use_container_width=True, hide_index=True)


with st.expander(f'Importância relativa dos Atributos – {uano}', True):
    feature_importance = (ols_df
                          .query('Variável!="cons"')
                          .assign(vl = lambda x: abs(x.Coeficiente),
                                  nm = lambda x: (x.vl - x.vl.min())/(x.vl.max() - x.vl.min())*100,
                                  Importância = lambda x: where(x.Coeficiente<0, x.nm*(-1), x.nm).round(3))
                          .sort_values('Importância')
                          [['Variável', 'Coeficiente', 'P-valor', 'Importância']]
                          )
    
    fig = px.bar(feature_importance, y='Variável', x='Importância',
                 orientation='h',
                 labels={'Variável':'Atributo', 'Importância': 'Importância (%)'},
                 title=f"Importância relativa dos atributos no modelo")
    st.plotly_chart(fig, use_container_width=True)
    
    st.dataframe(feature_importance, use_container_width=True, hide_index=True)