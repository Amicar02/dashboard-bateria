import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

def gerar_relatorio_html(investimento=200000):
    print("A carregar os dados...")
    file_path = "c:\\Users\\MC81\\Desktop\\Andre\\resultados_otimizacao.csv"
    if not os.path.exists(file_path):
        print("Erro: Ficheiro resultados_otimizacao.csv não encontrado.")
        return

    df = pd.read_csv(file_path)
    df['Datetime'] = pd.to_datetime(df['Data'] + ' ' + df['Hora'])
    df['Mês'] = df['Datetime'].dt.month
    df['Dia_da_Semana'] = df['Datetime'].dt.dayofweek
    df['Hora_do_Dia'] = df['Datetime'].dt.hour
    
    dias_map = {0: 'Segunda', 1: 'Terça', 2: 'Quarta', 3: 'Quinta', 4: 'Sexta', 5: 'Sábado', 6: 'Domingo'}
    df['Nome_Dia_Semana'] = df['Dia_da_Semana'].map(dias_map)
    df['Nome_Dia_Semana'] = pd.Categorical(df['Nome_Dia_Semana'], categories=dias_map.values(), ordered=True)

    # 1. KPIs
    custo_sem = df['Custo_Sem_Bateria_Eur'].sum()
    custo_com = df['Custo_Com_Bateria_Eur'].sum()
    poupanca_total = custo_sem - custo_com
    payback_anos = investimento / poupanca_total if poupanca_total > 0 else 0
    roi = (poupanca_total / investimento) * 100 if investimento > 0 else 0

    # 2. Gráficos
    print("A gerar os gráficos...")
    df_mes = df.groupby('Mês')[['Custo_Sem_Bateria_Eur', 'Custo_Com_Bateria_Eur']].sum().reset_index()
    df_mes['Poupança_Mensal'] = df_mes['Custo_Sem_Bateria_Eur'] - df_mes['Custo_Com_Bateria_Eur']
    
    fig_custos = go.Figure()
    fig_custos.add_trace(go.Bar(x=df_mes['Mês'], y=df_mes['Custo_Sem_Bateria_Eur'], name='Sem Bateria', marker_color='#EF553B'))
    fig_custos.add_trace(go.Bar(x=df_mes['Mês'], y=df_mes['Custo_Com_Bateria_Eur'], name='Com Bateria', marker_color='#00CC96'))
    fig_custos.update_layout(title="Custos por Mês (€)", barmode='group')

    fig_poupanca = px.bar(df_mes, x='Mês', y='Poupança_Mensal', title="Poupança Mensal (€)", color_discrete_sequence=['#636EFA'])

    df_dia = df.groupby('Nome_Dia_Semana', observed=True)['Consumo_kWh'].mean().reset_index()
    fig_dia = px.line(df_dia, x='Nome_Dia_Semana', y='Consumo_kWh', title="Consumo Médio: Dia da Semana", markers=True)
    fig_dia.update_traces(line_color='#AB63FA', line_width=3, marker_size=8)

    df_hora = df.groupby('Hora_do_Dia')['Consumo_kWh'].mean().reset_index()
    fig_hora = px.bar(df_hora, x='Hora_do_Dia', y='Consumo_kWh', title="Perfil de Consumo Médio (Hora)")

    # Simulação de 1 Semana Exemplo
    uma_semana = df.head(4 * 24 * 7).copy()
    uma_semana['Consumo_Liquido'] = (uma_semana['Consumo_kWh'] - uma_semana['Producao_kWh']).clip(lower=0)

    fig_mix = go.Figure()
    fig_mix.add_trace(go.Bar(x=uma_semana['Datetime'], y=uma_semana['Descarga_Bateria_kWh'], name='Bateria (Descarregamento)', marker_color='#FFA15A'))
    fig_mix.add_trace(go.Bar(x=uma_semana['Datetime'], y=uma_semana['Compra_Rede_kWh'], name='Rede (Compra)', marker_color='#EF553B'))
    fig_mix.add_trace(go.Scatter(x=uma_semana['Datetime'], y=uma_semana['Consumo_Liquido'], mode='lines', name='Consumo Líquido', line=dict(color='black', width=2)))
    fig_mix.update_layout(title="Origem da Energia face ao Consumo (Exemplo 1ª Semana)", barmode='stack')

    # Exportar os gráficos para HTML
    print("A construir o ficheiro HTML...")
    html_template = f"""
    <html>
    <head>
        <meta charset="utf-8">
        <title>Relatório de Baterias</title>
        <style>
            body {{ font-family: Arial, sans-serif; background-color: #f4f4f9; color: #333; margin: 0; padding: 20px; }}
            .container {{ max-width: 1200px; margin: auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); }}
            h1 {{ color: #2c3e50; text-align: center; }}
            .kpi-container {{ display: flex; justify-content: space-around; background-color: #ecf0f1; padding: 20px; border-radius: 8px; margin-bottom: 30px; }}
            .kpi {{ text-align: center; }}
            .kpi h3 {{ margin: 0; color: #7f8c8d; font-size: 14px; text-transform: uppercase; }}
            .kpi p {{ margin: 10px 0 0 0; font-size: 24px; font-weight: bold; color: #2980b9; }}
            .charts-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 40px; }}
            .chart-full {{ width: 100%; margin-bottom: 40px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🔋 Relatório de Otimização e Viabilidade de Baterias</h1>
            
            <div class="kpi-container">
                <div class="kpi"><h3>Investimento Base</h3><p>{investimento:,.0f} €</p></div>
                <div class="kpi"><h3>Custo Sem Bateria</h3><p>{custo_sem:,.0f} €</p></div>
                <div class="kpi"><h3>Custo Com Bateria</h3><p>{custo_com:,.0f} €</p></div>
                <div class="kpi"><h3>Poupança Anual</h3><p style="color:#27ae60;">{poupanca_total:,.0f} €</p></div>
                <div class="kpi"><h3>Payback Estimado</h3><p>{payback_anos:.1f} Anos</p></div>
                <div class="kpi"><h3>ROI Anual</h3><p>{roi:.1f} %</p></div>
            </div>

            <div class="charts-grid">
                <div>{fig_custos.to_html(full_html=False, include_plotlyjs='cdn')}</div>
                <div>{fig_poupanca.to_html(full_html=False, include_plotlyjs=False)}</div>
            </div>

            <div class="charts-grid">
                <div>{fig_dia.to_html(full_html=False, include_plotlyjs=False)}</div>
                <div>{fig_hora.to_html(full_html=False, include_plotlyjs=False)}</div>
            </div>
            
            <h2>Comportamento (Exemplo da 1ª Semana)</h2>
            <div class="chart-full">
                {fig_mix.to_html(full_html=False, include_plotlyjs=False)}
            </div>
            
            <p style="text-align:center; color:#95a5a6; margin-top:40px;">Relatório gerado automaticamente. Todos os gráficos são interativos.</p>
        </div>
    </body>
    </html>
    """

    output_path = "c:\\Users\\MC81\\Desktop\\Andre\\Relatorio_Baterias.html"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_template)
    
    print(f"✅ Concluído! O ficheiro '{output_path}' foi criado com sucesso.")

if __name__ == "__main__":
    gerar_relatorio_html()
