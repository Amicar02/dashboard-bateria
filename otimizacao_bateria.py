import pandas as pd
import pulp
import time
import os

def optimizar_bateria(
    path_dir,
    potencia_contratada_kw=630,
    potencia_descarga_kw=500,
    potencia_carga_kw=500,
    capacidade_bateria_kwh=1044
):
    print(f"A ler ficheiros do diretório: {path_dir}")
    file_consumo = os.path.join(path_dir, "consumo_kWh.txt")
    file_producao = os.path.join(path_dir, "producao_kWh.txt")
    file_mibel = os.path.join(path_dir, "mibel.txt")
    file_hours = os.path.join(path_dir, "hours.txt")
    file_timestamp = os.path.join(path_dir, "timestamp.txt")

    # Ler dados
    df_consumo = pd.read_csv(file_consumo, header=None, names=['Consumo_kWh'])
    df_producao = pd.read_csv(file_producao, header=None, names=['Producao_kWh'])
    df_mibel = pd.read_csv(file_mibel, header=None, names=['Mibel_Eur_kWh'])
    df_hours = pd.read_csv(file_hours, header=None, names=['Hora'])
    df_timestamp = pd.read_csv(file_timestamp, header=None, names=['Data'])

    # Combinar tudo num único DataFrame
    df = pd.concat([df_timestamp, df_hours, df_consumo, df_producao, df_mibel], axis=1)
    
    # Parâmetros
    dt = 0.25  # 15 minutos = 0.25 horas
    max_energia_rede_kwh = potencia_contratada_kw * dt
    max_carga_kwh = potencia_carga_kw * dt
    max_descarga_kwh = potencia_descarga_kw * dt
    soc_min = 0.0
    soc_max = capacidade_bateria_kwh

    N = len(df)
    C = df['Consumo_kWh'].values
    P = df['Producao_kWh'].values
    M = df['Mibel_Eur_kWh'].values

    print(f"Foram lidos {N} registos (intervalos de 15 min). A iniciar formulação do problema de otimização...")
    start_time = time.time()

    # Criação do Problema (Minimizar Custos)
    prob = pulp.LpProblem("Otimizacao_Arbitragem_Bateria", pulp.LpMinimize)

    # Variáveis de Decisão
    # O uso de dicionários é mais eficiente para o PuLP
    charge_vars = pulp.LpVariable.dicts("Carga", range(N), lowBound=0, upBound=max_carga_kwh)
    discharge_vars = pulp.LpVariable.dicts("Descarga", range(N), lowBound=0, upBound=max_descarga_kwh)
    soc_vars = pulp.LpVariable.dicts("SoC", range(N), lowBound=soc_min, upBound=soc_max)
    grid_buy_vars = pulp.LpVariable.dicts("Compra_Rede", range(N), lowBound=0, upBound=max_energia_rede_kwh)
    grid_sell_vars = pulp.LpVariable.dicts("Venda_Rede", range(N), lowBound=0, upBound=max_energia_rede_kwh)

    # Função Objetivo:
    # 1. Minimizar o custo de comprar à rede: Mibel * Compra_Rede
    # 2. Penalização muito ligeira na carga/descarga (ex: 0.0001 €/kWh) para simular custo de degradação
    #    e evitar que a bateria carregue e descarregue ao mesmo tempo desnecessariamente.
    custo_degradacao = 0.0001
    prob += pulp.lpSum([
        M[t] * grid_buy_vars[t] + 
        custo_degradacao * charge_vars[t] + 
        custo_degradacao * discharge_vars[t] 
        for t in range(N)
    ])

    # Restrições
    for t in range(N):
        # 1. Balanço de Energia:
        # O que entra/sai da rede + O que sai/entra da bateria = Necessidade líquida (Consumo - Produção)
        prob += grid_buy_vars[t] - grid_sell_vars[t] + discharge_vars[t] - charge_vars[t] == C[t] - P[t]

        # 2. Atualização do Estado de Carga (SoC):
        if t == 0:
            # Assumimos que a bateria começa vazia
            prob += soc_vars[t] == charge_vars[t] - discharge_vars[t]
        else:
            prob += soc_vars[t] == soc_vars[t-1] + charge_vars[t] - discharge_vars[t]

    print(f"Formulação concluída em {time.time() - start_time:.2f} segundos. A resolver...")

    # Resolver o Problema (usando o solver open-source default do PuLP - CBC)
    solve_start = time.time()
    prob.solve()
    print(f"Resolução concluída em {time.time() - solve_start:.2f} segundos.")
    print(f"Status da Solução: {pulp.LpStatus[prob.status]}")

    # Extrair resultados para o DataFrame
    df['Carga_Bateria_kWh'] = [charge_vars[t].varValue for t in range(N)]
    df['Descarga_Bateria_kWh'] = [discharge_vars[t].varValue for t in range(N)]
    df['SoC_kWh'] = [soc_vars[t].varValue for t in range(N)]
    df['Compra_Rede_kWh'] = [grid_buy_vars[t].varValue for t in range(N)]
    df['Venda_Rede_kWh'] = [grid_sell_vars[t].varValue for t in range(N)]
    
    # Calcular custos sem e com bateria
    df['Custo_Sem_Bateria_Eur'] = df.apply(lambda row: max(0, row['Consumo_kWh'] - row['Producao_kWh']) * row['Mibel_Eur_kWh'], axis=1)
    df['Custo_Com_Bateria_Eur'] = df['Compra_Rede_kWh'] * df['Mibel_Eur_kWh']

    custo_total_sem = df['Custo_Sem_Bateria_Eur'].sum()
    custo_total_com = df['Custo_Com_Bateria_Eur'].sum()
    poupanca = custo_total_sem - custo_total_com

    print("-" * 50)
    print(f"Custo Anual (Apenas Mercado Diário) SEM bateria: {custo_total_sem:.2f} €")
    print(f"Custo Anual (Apenas Mercado Diário) COM bateria: {custo_total_com:.2f} €")
    print(f"Poupança Estimada: {poupanca:.2f} €")
    print("-" * 50)

    # Guardar resultados
    output_file = os.path.join(path_dir, "resultados_otimizacao.csv")
    df.to_csv(output_file, index=False)
    print(f"Resultados detalhados guardados em: {output_file}")

if __name__ == "__main__":
    # O user deve garantir que faz: pip install pandas pulp
    diretorio_dados = r"c:\Users\MC81\Desktop\Andre"
    optimizar_bateria(diretorio_dados)
