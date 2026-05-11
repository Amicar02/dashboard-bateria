import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

# Configuração da Página
st.set_page_config(page_title="Dashboard Otimização de Bateria", layout="wide", page_icon="🔋")

st.title("🔋 Dashboard de Otimização de Arbitragem de Bateria")
st.markdown("Análise dos resultados de simulação de 1 ano de consumo e impacto financeiro com bateria.")

# --- 1. Carregamento de Dados ---
@st.cache_data
def load_data():
    # Usar caminho relativo para funcionar na Cloud e em qualquer PC
    file_path = "resultados_otimizacao.csv"
    if not os.path.exists(file_path):
        st.error(f"Ficheiro {file_path} não encontrado. Por favor corra o script de otimização primeiro.")
        return None
    
    df = pd.read_csv(file_path)
    # Criar coluna Datetime
    df['Datetime'] = pd.to_datetime(df['Data'] + ' ' + df['Hora'])
    # Extrair atributos temporais
    df['Mês'] = df['Datetime'].dt.month
    df['Dia_da_Semana'] = df['Datetime'].dt.dayofweek # 0=Segunda, 6=Domingo
    df['Hora_do_Dia'] = df['Datetime'].dt.hour
    
    # Mapear dias da semana
    dias_map = {0: 'Segunda', 1: 'Terça', 2: 'Quarta', 3: 'Quinta', 4: 'Sexta', 5: 'Sábado', 6: 'Domingo'}
    df['Nome_Dia_Semana'] = df['Dia_da_Semana'].map(dias_map)
    # Ordem categórica para dias
    df['Nome_Dia_Semana'] = pd.Categorical(df['Nome_Dia_Semana'], categories=['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo'], ordered=True)
    
    return df

df = load_data()

if df is not None:
    # --- 2. Input de Investimento ---
    st.sidebar.header("Parâmetros Financeiros")
    investimento = st.sidebar.number_input("Valor do Investimento (€):", min_value=0.0, value=200000.0, step=10000.0, format="%.2f")

    # --- 3. KPIs Principais ---
    custo_sem = df['Custo_Sem_Bateria_Eur'].sum()
    custo_com = df['Custo_Com_Bateria_Eur'].sum()
    poupanca_total = custo_sem - custo_com
    
    payback_anos = investimento / poupanca_total if poupanca_total > 0 else 0
    roi = (poupanca_total / investimento) * 100 if investimento > 0 else 0

    st.subheader("Resumo Anual")
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Custo S/ Bateria", f"{custo_sem:,.2f} €")
    col2.metric("Custo C/ Bateria", f"{custo_com:,.2f} €")
    col3.metric("Poupança Anual", f"{poupanca_total:,.2f} €", delta=f"{poupanca_total:,.2f} €")
    col4.metric("Payback Estimado", f"{payback_anos:.1f} anos", delta="- Rápido" if payback_anos < 7 else "Lento", delta_color="inverse")
    col5.metric("ROI Anual", f"{roi:.1f} %")

    st.markdown("---")

    # --- 4. Análise Mensal ---
    st.subheader("Análise Financeira Mensal")
    
    # Agrupar por mês
    df_mes = df.groupby('Mês')[['Custo_Sem_Bateria_Eur', 'Custo_Com_Bateria_Eur']].sum().reset_index()
    df_mes['Poupança_Mensal'] = df_mes['Custo_Sem_Bateria_Eur'] - df_mes['Custo_Com_Bateria_Eur']
    
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        # Gráfico: Custos Comparados Mensais
        fig_custos = go.Figure()
        fig_custos.add_trace(go.Bar(x=df_mes['Mês'], y=df_mes['Custo_Sem_Bateria_Eur'], name='Custo Sem Bateria', marker_color='#EF553B'))
        fig_custos.add_trace(go.Bar(x=df_mes['Mês'], y=df_mes['Custo_Com_Bateria_Eur'], name='Custo Com Bateria', marker_color='#00CC96'))
        fig_custos.update_layout(title="Custos por Mês (€)", barmode='group', xaxis_title="Mês", yaxis_title="Custo (€)")
        st.plotly_chart(fig_custos, use_container_width=True)

    with col_chart2:
        # Gráfico: Poupança Mensal
        fig_poupanca = px.bar(df_mes, x='Mês', y='Poupança_Mensal', title="Poupança Gerada por Mês (€)", text_auto='.2s', color_discrete_sequence=['#636EFA'])
        fig_poupanca.update_layout(xaxis_title="Mês", yaxis_title="Poupança (€)")
        st.plotly_chart(fig_poupanca, use_container_width=True)

    st.markdown("---")

    # --- 5. Análise de Consumo (Estatística e Previsão) ---
    st.subheader("Perfil de Consumo da Fábrica")
    
    col_c1, col_c2 = st.columns(2)
    
    with col_c1:
        # Consumo por Dia da Semana
        df_dia = df.groupby('Nome_Dia_Semana', observed=True)['Consumo_kWh'].mean().reset_index()
        fig_dia = px.line(df_dia, x='Nome_Dia_Semana', y='Consumo_kWh', title="Consumo Médio por Dia da Semana (15 min)", markers=True)
        fig_dia.update_traces(line_color='#AB63FA', line_width=3, marker_size=8)
        fig_dia.update_layout(xaxis_title="Dia da Semana", yaxis_title="Consumo Médio (kWh/15min)")
        st.plotly_chart(fig_dia, use_container_width=True)
        
    with col_c2:
        # Consumo por Hora do Dia
        df_hora = df.groupby('Hora_do_Dia')['Consumo_kWh'].mean().reset_index()
        fig_hora = px.bar(df_hora, x='Hora_do_Dia', y='Consumo_kWh', title="Perfil de Consumo Médio Diário (por Hora)", color='Consumo_kWh', color_continuous_scale='Sunsetdark')
        fig_hora.update_layout(xaxis_title="Hora do Dia (0-23)", yaxis_title="Consumo Médio (kWh)")
        st.plotly_chart(fig_hora, use_container_width=True)

    st.markdown("---")

    # --- 6. Visualização do Comportamento da Bateria ---
    st.subheader("Simulador do Comportamento Diário da Bateria")
    st.markdown("Escolha um intervalo de datas para ver como a bateria se carrega quando a energia está barata (ou há excesso solar) e descarrega quando a energia está cara.")
    
    min_date = df['Datetime'].min().date()
    max_date = df['Datetime'].max().date()
    
    selected_date = st.slider("Selecione um dia para analisar:", min_value=min_date, max_value=max_date, value=min_date)
    
    df_day = df[df['Datetime'].dt.date == selected_date].copy()
    
    if not df_day.empty:
        fig_bat = go.Figure()
        
        # Eixo Y1 (SoC e Potências)
        fig_bat.add_trace(go.Scatter(x=df_day['Datetime'], y=df_day['SoC_kWh'], mode='lines', name='Estado da Bateria (SoC)', line=dict(color='orange', width=3)))
        fig_bat.add_trace(go.Bar(x=df_day['Datetime'], y=df_day['Carga_Bateria_kWh'], name='Carregamento (kWh)', marker_color='green', opacity=0.6))
        fig_bat.add_trace(go.Bar(x=df_day['Datetime'], y=-df_day['Descarga_Bateria_kWh'], name='Descarregamento (kWh)', marker_color='red', opacity=0.6))
        
        # Eixo Y2 (Preço Mibel)
        fig_bat.add_trace(go.Scatter(x=df_day['Datetime'], y=df_day['Mibel_Eur_kWh'], mode='lines', name='Preço Mibel (€/kWh)', yaxis='y2', line=dict(color='blue', width=2, dash='dot')))
        
        fig_bat.update_layout(
            title=f"Comportamento da Bateria no dia {selected_date}",
            xaxis_title="Hora",
            yaxis=dict(title="Energia (kWh)", side="left"),
            yaxis2=dict(title="Preço Mibel (€/kWh)", side="right", overlaying="y", showgrid=False),
            barmode='relative',
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig_bat, use_container_width=True)

        # --- Novo Gráfico: Cobertura do Consumo Líquido ---
        # Consumo Líquido = max(0, Consumo - Producao)
        df_day['Consumo_Liquido'] = (df_day['Consumo_kWh'] - df_day['Producao_kWh']).clip(lower=0)
        
        fig_mix = go.Figure()
        # Barras para a Bateria e Rede (Stacked) para mostrar como cobrem o consumo líquido
        fig_mix.add_trace(go.Bar(x=df_day['Datetime'], y=df_day['Descarga_Bateria_kWh'], name='Bateria (Descarregamento)', marker_color='#FFA15A'))
        fig_mix.add_trace(go.Bar(x=df_day['Datetime'], y=df_day['Compra_Rede_kWh'], name='Rede (Compra)', marker_color='#EF553B'))
        # Linha para o Consumo Líquido
        fig_mix.add_trace(go.Scatter(x=df_day['Datetime'], y=df_day['Consumo_Liquido'], mode='lines', name='Consumo Líquido (Fábrica - Solar)', line=dict(color='white', width=3)))
        
        fig_mix.update_layout(
            title=f"Origem da Energia face ao Consumo Líquido ({selected_date})",
            xaxis_title="Hora",
            yaxis_title="Energia (kWh)",
            barmode='stack',
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig_mix, use_container_width=True)

        # --- Resumo Estatístico do Dia ---
        st.markdown(f"### Resumo do dia {selected_date}")
        
        # Métricas Financeiras
        custo_sem_dia = df_day['Custo_Sem_Bateria_Eur'].sum()
        custo_com_dia = df_day['Custo_Com_Bateria_Eur'].sum()
        poup_dia = custo_sem_dia - custo_com_dia
        
        # Métricas Energéticas
        cons_total_dia = df_day['Consumo_kWh'].sum()
        prod_solar_dia = df_day['Producao_kWh'].sum()
        descarga_dia = df_day['Descarga_Bateria_kWh'].sum()
        compra_dia = df_day['Compra_Rede_kWh'].sum()
        
        col_d1, col_d2 = st.columns(2)
        with col_d1:
            st.info(f"**Impacto Financeiro:**\n\n"
                    f"💸 **Custo sem Bateria:** {custo_sem_dia:.2f} €\n\n"
                    f"💰 **Custo com Bateria:** {custo_com_dia:.2f} €\n\n"
                    f"🏆 **Poupança no dia:** {poup_dia:.2f} €")
        with col_d2:
            perc_bat = (descarga_dia / (descarga_dia + compra_dia) * 100) if (descarga_dia + compra_dia) > 0 else 0
            perc_rede = 100 - perc_bat if (descarga_dia + compra_dia) > 0 else 0
            
            st.success(f"**Balanço Energético:**\n\n"
                       f"🏭 **Consumo da Fábrica:** {cons_total_dia:.1f} kWh | ☀️ **Produção Solar:** {prod_solar_dia:.1f} kWh\n\n"
                       f"🔋 **Suprido pela Bateria:** {descarga_dia:.1f} kWh ({perc_bat:.1f}%)\n\n"
                       f"🔌 **Suprido pela Rede:** {compra_dia:.1f} kWh ({perc_rede:.1f}%)")
