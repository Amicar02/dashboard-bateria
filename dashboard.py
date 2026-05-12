import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

# Configuração da Página
st.set_page_config(page_title="Dashboard Otimização de Bateria", layout="wide", page_icon="🔋")

st.title("🔋 Dashboard de Otimização de Baterias")
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
    st.header("Parâmetros Financeiros")
    investimento = st.number_input("Valor do Investimento (€):", min_value=0.0, value=217960.0, step=1000.0, format="%.2f")

    # --- 3. KPIs Principais ---
    custo_sem = df['Custo_Sem_Bateria_Eur'].sum()
    custo_com = df['Custo_Com_Bateria_Eur'].sum()
    poupanca_total = custo_sem - custo_com
    
    payback_anos = investimento / poupanca_total if poupanca_total > 0 else 0
    roi = (poupanca_total / investimento) * 100 if investimento > 0 else 0

    st.subheader("Resumo Anual")
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Custo S/ Bateria", f"{custo_sem:,.0f} €")
    col2.metric("Custo C/ Bateria", f"{custo_com:,.0f} €")
    col3.metric("Poupança Anual", f"{poupanca_total:,.0f} €", delta=f"{poupanca_total:,.0f} €")
    col4.metric("Payback Estimado", f"{payback_anos:.1f} anos", delta="- Bom" if payback_anos < 10 else "Lento", delta_color="inverse")
    col5.metric("ROI Anual", f"{roi:.1f} %")

    st.markdown("---")

    # --- 4. Análise Mensal ---
    st.subheader("Análise Financeira Mensal")
    
    # Agrupar por mês
    df_mes = df.groupby('Mês')[['Custo_Sem_Bateria_Eur', 'Custo_Com_Bateria_Eur']].sum().reset_index()
    df_mes['Poupança_Mensal'] = df_mes['Custo_Sem_Bateria_Eur'] - df_mes['Custo_Com_Bateria_Eur']
    
    # Mapear meses para nomes
    meses_map = {1: 'Jan', 2: 'Fev', 3: 'Mar', 4: 'Abr', 5: 'Mai', 6: 'Jun', 
                 7: 'Jul', 8: 'Ago', 9: 'Set', 10: 'Out', 11: 'Nov', 12: 'Dez'}
    meses_extenso_map = {1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril', 5: 'Maio', 6: 'Junho', 
                         7: 'Julho', 8: 'Agosto', 9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'}
    df_mes['Nome_Mes'] = df_mes['Mês'].map(meses_map)
    df_mes['Nome_Mes'] = pd.Categorical(df_mes['Nome_Mes'], categories=list(meses_map.values()), ordered=True)
    df_mes['Nome_Mes_Extenso'] = df_mes['Mês'].map(meses_extenso_map)
    
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        # Gráfico: Custos Comparados Mensais
        fig_custos = go.Figure()
        fig_custos.add_trace(go.Scatter(
            x=df_mes['Nome_Mes'], y=df_mes['Custo_Sem_Bateria_Eur'], mode='lines+markers', name='Custo original', line=dict(color='#EF553B', width=3), marker=dict(size=8),
            customdata=df_mes[['Nome_Mes_Extenso']],
            hovertemplate="%{customdata[0]}<br>Custo original: %{y:,.0f} €<extra></extra>"
        ))
        fig_custos.add_trace(go.Scatter(
            x=df_mes['Nome_Mes'], y=df_mes['Custo_Com_Bateria_Eur'], mode='lines+markers', name='Novo custo', line=dict(color='#00CC96', width=3), marker=dict(size=8),
            customdata=df_mes[['Nome_Mes_Extenso']],
            hovertemplate="%{customdata[0]}<br>Novo custo: %{y:,.0f} €<extra></extra>"
        ))
        fig_custos.update_layout(title="Custos por Mês (€)", xaxis_title="Mês", yaxis_title="Custo (€)", hovermode='x unified')
        st.plotly_chart(fig_custos, use_container_width=True)

    with col_chart2:
        # Gráfico: Poupança Mensal
        fig_poupanca = px.bar(df_mes, x='Nome_Mes', y='Poupança_Mensal', title="Poupança Gerada por Mês (€)", text_auto='.2s', color_discrete_sequence=['#636EFA'], custom_data=['Nome_Mes_Extenso'])
        fig_poupanca.update_traces(hovertemplate="%{customdata[0]}<br>Poupança Mensal: %{y:,.0f} €<extra></extra>")
        fig_poupanca.update_layout(xaxis_title="Mês", yaxis_title="Poupança (€)")
        st.plotly_chart(fig_poupanca, use_container_width=True)

    st.markdown("---")

    # --- 5. Análise de Consumo (Estatística e Previsão) ---
    st.subheader("Perfil de Consumo da Fábrica")
    
    col_c1, col_c2 = st.columns(2)
    
    with col_c1:
        # Consumo Diário Total (soma das parcelas de 15 min, média por dia da semana)
        df_daily_total = df.groupby(df['Datetime'].dt.date)['Consumo_kWh'].sum().reset_index()
        df_daily_total['Datetime'] = pd.to_datetime(df_daily_total['Datetime'])
        
        dias_map = {0: 'Segunda', 1: 'Terça', 2: 'Quarta', 3: 'Quinta', 4: 'Sexta', 5: 'Sábado', 6: 'Domingo'}
        df_daily_total['Nome_Dia_Semana'] = df_daily_total['Datetime'].dt.dayofweek.map(dias_map)
        df_daily_total['Nome_Dia_Semana'] = pd.Categorical(df_daily_total['Nome_Dia_Semana'], categories=list(dias_map.values()), ordered=True)
        
        df_dia = df_daily_total.groupby('Nome_Dia_Semana', observed=True)['Consumo_kWh'].mean().reset_index()
        # Converter para MWh
        df_dia['Consumo_MWh'] = df_dia['Consumo_kWh'] / 1000
        
        fig_dia = px.line(df_dia, x='Nome_Dia_Semana', y='Consumo_MWh', title="Consumo Médio Diário da Fábrica", markers=True)
        fig_dia.update_traces(
            line_color='#AB63FA', line_width=3, marker_size=8,
            hovertemplate="%{x}<br>Consumo Médio Diário: %{y:.2f} MWh<extra></extra>"
        )
        fig_dia.update_layout(xaxis_title="Dia da Semana", yaxis_title="Consumo Total (MWh/dia)")
        st.plotly_chart(fig_dia, use_container_width=True)
        
    with col_c2:
        # Consumo por Hora do Dia
        df_hora = df.groupby('Hora_do_Dia')['Consumo_kWh'].mean().reset_index()
        # Como os dados são de 15 min, a energia horária média é a média de 15 min * 4
        df_hora['Consumo_Hora_kWh'] = df_hora['Consumo_kWh'] * 4
        
        # Criar texto de intervalo horário para o Hover
        df_hora['Intervalo_Horario'] = df_hora['Hora_do_Dia'].apply(lambda h: f"{h:02d}:00 - {(h+1)%24:02d}:00")
        
        fig_hora = px.bar(
            df_hora, x='Hora_do_Dia', y='Consumo_Hora_kWh', 
            title="Perfil de Consumo Médio Diário (por Hora)", 
            color='Consumo_Hora_kWh', color_continuous_scale='Sunsetdark',
            custom_data=['Intervalo_Horario']
        )
        fig_hora.update_traces(hovertemplate="%{customdata[0]}<br>Consumo Médio: %{y:.0f} kWh<extra></extra>")
        fig_hora.update_layout(
            xaxis_title="Horas (h)", 
            yaxis_title="Consumo Horário (kWh)",
            xaxis=dict(tickmode='linear', dtick=1) # Força a mostrar todas as horas no eixo
        )
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
        
        # Preparar percentagem e hover
        df_day['SoC_perc'] = (df_day['SoC_kWh'] / 1044) * 100
        df_day['Mibel_Eur_MWh'] = df_day['Mibel_Eur_kWh'] * 1000
        
        nome_dia = df_day['Nome_Dia_Semana'].iloc[0]
        
        # Eixo Y1 (SoC e Potências)
        fig_bat.add_trace(go.Scatter(x=df_day['Datetime'], y=df_day['SoC_perc'], mode='lines', name='Carga da Bateria (%)', customdata=df_day['SoC_kWh'], hovertemplate="%{x|%d/%m/%Y %H:%M}<br>Carga da Bateria (%): %{y:.1f}% (%{customdata:.0f} kWh)<extra></extra>", line=dict(color='orange', width=3)))
        fig_bat.add_trace(go.Bar(x=df_day['Datetime'], y=df_day['Carga_Bateria_kWh'], name='Energia Carregada (kWh)', hovertemplate="%{x|%d/%m/%Y %H:%M}<br>Energia Carregada (kWh): %{y:.1f} kWh<extra></extra>", marker_color='green', opacity=0.6))
        fig_bat.add_trace(go.Bar(x=df_day['Datetime'], y=-df_day['Descarga_Bateria_kWh'], name='Energia Descarregada (kWh)', customdata=df_day['Descarga_Bateria_kWh'], hovertemplate="%{x|%d/%m/%Y %H:%M}<br>Energia Descarregada (kWh): %{customdata:.1f} kWh<extra></extra>", marker_color='red', opacity=0.6))
        
        # Eixo Y2 (Preço Mibel em MWh)
        fig_bat.add_trace(go.Scatter(x=df_day['Datetime'], y=df_day['Mibel_Eur_MWh'], mode='lines', name='Preço de Mercado (€/MWh)', hovertemplate="%{x|%d/%m/%Y %H:%M}<br>Preço de Mercado (€/MWh): %{y:.2f} €/MWh<extra></extra>", yaxis='y2', line=dict(color='blue', width=2, dash='dot')))
        
        fig_bat.update_layout(
            title=f"Como a Bateria reagiu aos preços no dia {selected_date} ({nome_dia})",
            xaxis_title="Hora do Dia",
            yaxis=dict(title="Energia (kWh) / Nível (%)", side="left"),
            yaxis2=dict(title="Preço da Eletricidade (€/MWh)", side="right", overlaying="y", showgrid=False),
            barmode='relative',
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig_bat, use_container_width=True)

        # --- Novo Gráfico: Cobertura do Consumo Líquido ---
        # Consumo Líquido = max(0, Consumo - Producao)
        df_day['Consumo_Liquido'] = (df_day['Consumo_kWh'] - df_day['Producao_kWh']).clip(lower=0)
        
        # Separar Compra da Rede para a Fábrica vs Bateria
        df_day['Compra_Rede_Fábrica'] = (df_day['Consumo_Liquido'] - df_day['Descarga_Bateria_kWh']).clip(lower=0)
        df_day['Compra_Rede_Fábrica'] = df_day[['Compra_Rede_kWh', 'Compra_Rede_Fábrica']].min(axis=1)
        df_day['Compra_Rede_Bateria'] = df_day['Compra_Rede_kWh'] - df_day['Compra_Rede_Fábrica']
        
        fig_mix = go.Figure()
        # Barras para a Bateria e Rede (Stacked) para mostrar como cobrem o consumo líquido
        fig_mix.add_trace(go.Bar(x=df_day['Datetime'], y=df_day['Descarga_Bateria_kWh'], name='Energia Descarregada', hovertemplate="%{x|%d/%m/%Y %H:%M}<br>Energia Descarregada: %{y:.1f} kWh<extra></extra>", marker_color='#00CC96'))
        
        # Rede para a Fábrica
        fig_mix.add_trace(go.Bar(x=df_day['Datetime'], y=df_day['Compra_Rede_Fábrica'], name='Comprado à Rede (Para Fábrica)', hovertemplate="%{x|%d/%m/%Y %H:%M}<br>Comprado à Rede (Para Fábrica): %{y:.1f} kWh<extra></extra>", marker_color='#EF553B'))
        
        # Rede para Bateria (com tracejado)
        fig_mix.add_trace(go.Bar(x=df_day['Datetime'], y=df_day['Compra_Rede_Bateria'], name='Comprado à Rede (Para Bateria)', hovertemplate="%{x|%d/%m/%Y %H:%M}<br>Comprado à Rede (Para Bateria): %{y:.1f} kWh<extra></extra>", marker_color='#EF553B', marker_pattern_shape="/"))
        
        # Linha para o Consumo Líquido
        fig_mix.add_trace(go.Scatter(x=df_day['Datetime'], y=df_day['Consumo_Liquido'], mode='lines', name='Consumo Real (descontando Solar)', hovertemplate="%{x|%d/%m/%Y %H:%M}<br>Consumo Real (descontando Solar): %{y:.1f} kWh<extra></extra>", line=dict(color='#1F77B4', width=3)))
        
        fig_mix.update_layout(
            title=f"Como a Fábrica foi alimentada no dia {selected_date} ({nome_dia})",
            xaxis_title="Hora do Dia",
            yaxis_title="Energia Consumida (kWh)",
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
                    f"💸 **Custo sem Bateria:** {custo_sem_dia:.0f} €\n\n"
                    f"💰 **Custo com Bateria:** {custo_com_dia:.0f} €\n\n"
                    f"🏆 **Poupança no dia:** {poup_dia:.0f} €")
        with col_d2:
            perc_bat = (descarga_dia / (descarga_dia + compra_dia) * 100) if (descarga_dia + compra_dia) > 0 else 0
            perc_rede = 100 - perc_bat if (descarga_dia + compra_dia) > 0 else 0
            
            st.success(f"**Balanço Energético:**\n\n"
                       f"🏭 **Consumo da Fábrica:** {cons_total_dia:.0f} kWh | ☀️ **Producao UPAC nova:** {prod_solar_dia:.0f} kWh\n\n"
                       f"🔋 **Energia Descarregada (Bateria):** {descarga_dia:.0f} kWh ({perc_bat:.0f}%)\n\n"
                       f"🔌 **Energia Comprada (Rede):** {compra_dia:.0f} kWh ({perc_rede:.0f}%)")
