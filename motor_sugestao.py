import collections
import itertools

class MotorSugestaoLoteria:
    def __init__(self, nome_loteria="Mega-Sena"):
        """
        Inicializa o motor configurando as peculiaridades de cada loteria,
        incluindo tamanho do pool e restrições matemáticas específicas.
        """
        self.nome_loteria = nome_loteria.strip().lower().replace(" ", "").replace("-", "")
        
        # Configuração de jogo e cobertura para todas as loterias
        if "lotofacil" in self.nome_loteria or "lotofácil" in self.nome_loteria:
            self.total_numeros = 25
            self.game_size = 15
            self.pool_cobertura = 20
            self.modo_params = {
                "10": {"tamanho_grupo": 5, "qtd_grupos": 4, "combinar": 3},
                "5": {"tamanho_grupo": 3, "qtd_grupos": 7, "combinar": 5, "total_pool": 21}
            }
            self.ignorar_restricao_sequencia = True # Alta densidade permite sequências longas
            self.pool = list(range(1, self.total_numeros + 1))
        elif "lotomania" in self.nome_loteria:
            self.total_numeros = 100
            self.game_size = 50
            self.pool_cobertura = 80
            self.modo_params = {
                "10": {"tamanho_grupo": 10, "qtd_grupos": 8, "combinar": 5},
                "5": {"tamanho_grupo": 5, "qtd_grupos": 20, "combinar": 10, "total_pool": 100}
            }
            self.ignorar_restricao_sequencia = True # Alta densidade permite sequências longas
            self.pool = list(range(0, 100)) # Lotomania vai de 00 a 99
        elif "quina" in self.nome_loteria:
            self.total_numeros = 80
            self.game_size = 5
            self.pool_cobertura = 25
            self.modo_params = {
                "10": {"tamanho_grupo": 1, "qtd_grupos": 25, "combinar": 5},
                "5": {"tamanho_grupo": 1, "qtd_grupos": 25, "combinar": 5}
            }
            self.ignorar_restricao_sequencia = False
            self.pool = list(range(1, self.total_numeros + 1))
        elif "duplasena" in self.nome_loteria:
            self.total_numeros = 50
            self.game_size = 6
            self.pool_cobertura = 24
            self.modo_params = {
                "10": {"tamanho_grupo": 2, "qtd_grupos": 12, "combinar": 3},
                "5": {"tamanho_grupo": 3, "qtd_grupos": 8, "combinar": 2}
            }
            self.ignorar_restricao_sequencia = False
            self.pool = list(range(1, self.total_numeros + 1))
        elif "diadesorte" in self.nome_loteria:
            self.total_numeros = 31
            self.game_size = 7
            self.pool_cobertura = 21
            self.modo_params = {
                "10": {"tamanho_grupo": 1, "qtd_grupos": 21, "combinar": 7},
                "5": {"tamanho_grupo": 1, "qtd_grupos": 21, "combinar": 7}
            }
            self.ignorar_restricao_sequencia = False
            self.pool = list(range(1, self.total_numeros + 1))
        else: 
            # Padrão: Mega-Sena
            self.total_numeros = 60
            self.game_size = 6
            self.pool_cobertura = 24
            self.modo_params = {
                "10": {"tamanho_grupo": 2, "qtd_grupos": 12, "combinar": 3},
                "5": {"tamanho_grupo": 3, "qtd_grupos": 8, "combinar": 2}
            }
            self.ignorar_restricao_sequencia = False
            self.pool = list(range(1, self.total_numeros + 1))
            
        # Etapa 1: Zoneamento Espacial (Divisão em Terços D1, D2, D3)
        terco = self.total_numeros // 3
        pool_ordenado = sorted(self.pool)
        self.d1 = set(pool_ordenado[:terco])
        self.d2 = set(pool_ordenado[terco:2*terco])
        self.d3 = set(pool_ordenado[2*terco:])

    def _calcular_latencia_e_ciclos(self, historico):
        """
        Calcula o gap atual (latência) e a média dos gaps (ciclo de recorrência).
        """
        latencia_atual = {num: 0 for num in self.pool}
        media_gaps = {num: 0.0 for num in self.pool}
        
        for num in self.pool:
            gaps = []
            gap_contador = 0
            for sorteio in historico:
                if num in sorteio:
                    gaps.append(gap_contador)
                    gap_contador = 0
                else:
                    gap_contador += 1
            
            latencia_atual[num] = gap_contador 
            if gaps:
                media_gaps[num] = sum(gaps) / len(gaps)
            else:
                media_gaps[num] = gap_contador
                
        return latencia_atual, media_gaps

    def _calcular_tendencia_imediata(self, historico):
        """Média móvel dos últimos 3 sorteios (Vetor de Tendência)."""
        tendencia = {num: 0 for num in self.pool}
        janela = historico[-3:] if len(historico) >= 3 else historico
        for sorteio in janela:
            for num in sorteio:
                tendencia[num] += 1
        return tendencia

    def _calcular_coocorrencia(self, historico):
        """Matriz de pares históricos."""
        pares = collections.defaultdict(int)
        for sorteio in historico:
            for par in itertools.combinations(sorted(sorteio), 2):
                pares[par] += 1
        return pares

    def _filtro_sequencia(self, combinacao):
        """
        Filtro de Descoerência: Impede mais de 3 números consecutivos.
        Aplica a exceção correta para Lotofácil e Lotomania, onde sequências são normais.
        """
        if self.ignorar_restricao_sequencia:
            return True
            
        combinacao_ordenada = sorted(combinacao)
        consecutivos = 1
        for i in range(1, len(combinacao_ordenada)):
            if combinacao_ordenada[i] == combinacao_ordenada[i-1] + 1:
                consecutivos += 1
                if consecutivos > 3:
                    return False
            else:
                consecutivos = 1
        return True

    def gerar_sugestao(self, historico, quantidade_sugestao):
        """Gera a sugestão otimizada aplicando as 3 etapas de análise."""
        if not historico:
            return self.pool[:quantidade_sugestao], (0,0), (0,0,0)

        latencia_atual, media_gaps = self._calcular_latencia_e_ciclos(historico)
        tendencia = self._calcular_tendencia_imediata(historico)
        coocorrencia = self._calcular_coocorrencia(historico)

        pontuacao = {num: 0.0 for num in self.pool}

        for num in self.pool:
            score_ciclo = (latencia_atual[num] / media_gaps[num]) if media_gaps[num] > 0 else 0
            score_tendencia = tendencia[num] * 2.0
            score_pares = sum(qtd for par, qtd in coocorrencia.items() if num in par) * 0.1
            pontuacao[num] = score_ciclo + score_tendencia + score_pares

        numeros_ordenados = sorted(pontuacao.keys(), key=lambda n: pontuacao[n], reverse=True)
        
        sugestao_final = []
        pares_count = 0
        impares_count = 0
        d1_count, d2_count, d3_count = 0, 0, 0
        
        max_paridade = (quantidade_sugestao // 2) + 2 
        max_dimensao = (quantidade_sugestao // 3) + 3 
        
        for num in numeros_ordenados:
            if len(sugestao_final) >= quantidade_sugestao:
                break
                
            eh_par = (num % 2 == 0)
            if eh_par and pares_count >= max_paridade: continue
            if not eh_par and impares_count >= max_paridade: continue
                
            if num in self.d1 and d1_count >= max_dimensao: continue
            if num in self.d2 and d2_count >= max_dimensao: continue
            if num in self.d3 and d3_count >= max_dimensao: continue
            
            teste_sugestao = sugestao_final + [num]
            if not self._filtro_sequencia(teste_sugestao):
                continue
                
            sugestao_final.append(num)
            
            if eh_par: pares_count += 1
            else: impares_count += 1
            
            if num in self.d1: d1_count += 1
            elif num in self.d2: d2_count += 1
            elif num in self.d3: d3_count += 1

        if len(sugestao_final) < quantidade_sugestao:
            for num in numeros_ordenados:
                if num not in sugestao_final:
                    teste_sugestao = sugestao_final + [num]
                    if self._filtro_sequencia(teste_sugestao):
                        sugestao_final.append(num)
                if len(sugestao_final) >= quantidade_sugestao:
                    break

        return sorted(sugestao_final), (pares_count, impares_count), (d1_count, d2_count, d3_count)

    def _calcular_frequencias(self, historico):
        """Calcula a frequência total de cada número no histórico."""
        frequencias = {num: 0 for num in self.pool}
        for sorteio in historico:
            for num in sorteio:
                if num in frequencias:
                    frequencias[num] += 1
        return frequencias

    def dividir_em_grupos_coocorrencia(self, numeros, tamanho_grupo, coocorrencia):
        """
        Divide a list/set of numbers into groups of a fixed size,
        maximizing the co-occurrence of numbers within each group.
        """
        disponiveis = set(numeros)
        grupos = []
        
        while len(disponiveis) >= tamanho_grupo:
            grupo_atual = []
            
            # Find the pair with highest co-occurrence among available
            melhor_par = None
            max_cooc = -1
            for a, b in itertools.combinations(disponiveis, 2):
                par_key = (min(a, b), max(a, b))
                cooc = coocorrencia.get(par_key, 0)
                if cooc > max_cooc:
                    max_cooc = cooc
                    melhor_par = (a, b)
            
            if melhor_par and max_cooc > 0:
                grupo_atual.extend(melhor_par)
                disponiveis.remove(melhor_par[0])
                disponiveis.remove(melhor_par[1])
            else:
                elem = list(disponiveis)[0]
                grupo_atual.append(elem)
                disponiveis.remove(elem)
                
            # Fill group
            while len(grupo_atual) < tamanho_grupo and disponiveis:
                melhor_cand = None
                max_score = -1
                for cand in disponiveis:
                    score = sum(coocorrencia.get((min(cand, x), max(cand, x)), 0) for x in grupo_atual)
                    if score > max_score:
                        max_score = score
                        melhor_cand = cand
                if melhor_cand is not None:
                    grupo_atual.append(melhor_cand)
                    disponiveis.remove(melhor_cand)
                else:
                    break
                    
            grupos.append(sorted(grupo_atual))
            
        if disponiveis:
            grupos.append(sorted(list(disponiveis)))
            
        return grupos

    def _obter_espelho(self, num):
        """Retorna o número espelho de num (ex: 12 -> 21, 09 -> 90)."""
        num_str = str(num).zfill(2)
        mirror_str = num_str[::-1]
        return int(mirror_str)

    def dividir_em_grupos_inteligentes(self, numeros, tamanho_grupo, coocorrencia, historico):
        """
        Divide um pool de dezenas em grupos de tamanho_grupo de forma inteligente para Lotomania.
        Aplica espelhamento, aproximação e equilíbrio de coocorrência (saíram juntos vs. não saíram).
        """
        disponiveis = set(numeros)
        grupos = []
        
        # 1. Calcular frequências e números mais sorteados nos sorteios mais recentes (últimos 10)
        frequencias = self._calcular_frequencias(historico)
        ultimos_sorteios = historico[-10:] if len(historico) >= 10 else historico
        frequencias_recentes = {num: 0 for num in self.pool}
        for sorteio in ultimos_sorteios:
            for num in sorteio:
                if num in frequencias_recentes:
                    frequencias_recentes[num] += 1
                    
        # Vizinhos dos números mais frequentes nos últimos sorteios
        numeros_quentes = sorted(frequencias_recentes.keys(), key=lambda n: frequencias_recentes[n], reverse=True)[:15]
        vizinhos_quentes = set()
        for n in numeros_quentes:
            vizinhos_quentes.add((n - 1) % 100)
            vizinhos_quentes.add((n + 1) % 100)
            vizinhos_quentes.add((n - 2) % 100)
            vizinhos_quentes.add((n + 2) % 100)
            
        # 2. Criar matriz de afinidade/similaridade
        affinity = {}
        for a in disponiveis:
            affinity[a] = {}
            espelho_a = self._obter_espelho(a)
            for b in disponiveis:
                if a == b:
                    continue
                score = 0.0
                # Coocorrência histórica
                par_key = (min(a, b), max(a, b))
                score += coocorrencia.get(par_key, 0) * 1.5
                
                # Espelhamento
                if b == espelho_a:
                    score += 15.0 # Forte bônus para espelhados no mesmo grupo
                
                # Proximidade de auto-espelhados (ex: 11 e 22)
                if a % 11 == 0 and b % 11 == 0:
                    score += 10.0 # Bônus para manter dezenas auto-espelhadas próximas
                    
                # Aproximação geográfica e de vizinhança
                if abs(a - b) in (1, 2):
                    score += 5.0
                if abs(a - b) in (10, 20): # Mesma coluna no volante
                    score += 3.0
                    
                # Aproximação por tendência de sorteios recentes
                if b in vizinhos_quentes:
                    score += 4.0
                    
                affinity[a][b] = score

        # 3. Formação dos grupos
        # Ordenar os disponíveis por frequência histórica geral para usar os dezenas-semente mais quentes
        ordenados_por_freq = sorted(list(disponiveis), key=lambda n: frequencias.get(n, 0), reverse=True)
        
        while len(disponiveis) >= tamanho_grupo:
            grupo_atual = []
            
            # Escolher a semente do grupo (elemento disponível com maior frequência histórica)
            semente = None
            for num in ordenados_por_freq:
                if num in disponiveis:
                    semente = num
                    break
            if semente is None:
                semente = list(disponiveis)[0]
                
            grupo_atual.append(semente)
            disponiveis.remove(semente)
            
            # Preencher o grupo de forma intercalada: metade afinidade máxima, metade diversidade máxima
            slots_restantes = tamanho_grupo - 1
            for slot in range(slots_restantes):
                if not disponiveis:
                    break
                    
                # Se slot for par, escolhe afinidade máxima (saíram juntos, espelho, aproximação)
                if slot % 2 == 0:
                    melhor_cand = None
                    max_score = -9999.0
                    for cand in disponiveis:
                        # Média de afinidade com os membros atuais do grupo
                        score = sum(affinity[cand].get(x, 0.0) for x in grupo_atual) / len(grupo_atual)
                        if score > max_score:
                            max_score = score
                            melhor_cand = cand
                    if melhor_cand is not None:
                        grupo_atual.append(melhor_cand)
                        disponiveis.remove(melhor_cand)
                # Se slot for ímpar, escolhe diversidade máxima (para ter dezenas que NÃO saíram juntos)
                else:
                    melhor_cand = None
                    min_score = 9999.0
                    for cand in disponiveis:
                        # Mínimo de coocorrência/afinidade
                        score = sum(coocorrencia.get((min(cand, x), max(cand, x)), 0) for x in grupo_atual) / len(grupo_atual)
                        if score < min_score:
                            min_score = score
                            melhor_cand = cand
                    if melhor_cand is not None:
                        grupo_atual.append(melhor_cand)
                        disponiveis.remove(melhor_cand)
                        
            grupos.append(sorted(grupo_atual))
            
        # Caso restem elementos (menos de tamanho_grupo)
        if disponiveis:
            grupos.append(sorted(list(disponiveis)))
            
        return grupos

    def _obter_params_cobertura_dinamico(self, quantidade_jogos):
        """
        Determina os parâmetros de agrupamento dinamicamente com base na quantidade de jogos solicitada,
        para garantir que haja combinações suficientes através de subdivisões.
        """
        if "lotomania" in self.nome_loteria:
            if quantidade_jogos <= 10:
                # 8 grupos de 10 -> C(8, 5) = 56 combinações
                return {"tamanho_grupo": 10, "qtd_grupos": 8, "combinar": 5, "total_pool": 80}
            elif quantidade_jogos <= 50:
                # 16 grupos de 5 -> C(16, 10) = 8.008 combinações
                return {"tamanho_grupo": 5, "qtd_grupos": 16, "combinar": 10, "total_pool": 80}
            elif quantidade_jogos <= 500:
                # 40 grupos de 2 -> C(40, 25) = 40.225.345.056 combinações
                return {"tamanho_grupo": 2, "qtd_grupos": 40, "combinar": 25, "total_pool": 80}
            else:
                # 80 grupos de 1 -> C(80, 50) combinações
                return {"tamanho_grupo": 1, "qtd_grupos": 80, "combinar": 50, "total_pool": 80}
                
        elif "megasena" in self.nome_loteria or "duplasena" in self.nome_loteria:
            if quantidade_jogos <= 28:
                return {"tamanho_grupo": 3, "qtd_grupos": 8, "combinar": 2, "total_pool": 24}
            elif quantidade_jogos <= 220:
                return {"tamanho_grupo": 2, "qtd_grupos": 12, "combinar": 3, "total_pool": 24}
            else:
                return {"tamanho_grupo": 1, "qtd_grupos": 24, "combinar": 6, "total_pool": 24}
                
        elif "lotofacil" in self.nome_loteria or "lotofácil" in self.nome_loteria:
            if quantidade_jogos <= 4:
                return {"tamanho_grupo": 5, "qtd_grupos": 4, "combinar": 3, "total_pool": 20}
            elif quantidade_jogos <= 21:
                return {"tamanho_grupo": 3, "qtd_grupos": 7, "combinar": 5, "total_pool": 21}
            else:
                return {"tamanho_grupo": 1, "qtd_grupos": 20, "combinar": 15, "total_pool": 20}
                
        elif "quina" in self.nome_loteria:
            return {"tamanho_grupo": 1, "qtd_grupos": 25, "combinar": 5, "total_pool": 25}
            
        elif "diadesorte" in self.nome_loteria:
            return {"tamanho_grupo": 1, "qtd_grupos": 21, "combinar": 7, "total_pool": 21}
            
        else:
            return {"tamanho_grupo": 1, "qtd_grupos": len(self.pool), "combinar": self.game_size, "total_pool": len(self.pool)}

    def _jogo_valido(self, jogo):
        """Verifica se o jogo de 50 dezenas atende a todos os critérios estritos da Lotomania."""
        if len(jogo) != 50:
            return False
        if len(set(jogo)) != 50:
            return False
            
        # 1. Paridade (max 27 dezenas pares ou ímpares)
        evens = len([x for x in jogo if x % 2 == 0])
        odds = 50 - evens
        if evens > 27 or odds > 27:
            return False
            
        # 2. Zonamento espacial (max 19 dezenas por terço)
        d1 = len([x for x in jogo if x in self.d1])
        d2 = len([x for x in jogo if x in self.d2])
        d3 = len([x for x in jogo if x in self.d3])
        if d1 > 19 or d2 > 19 or d3 > 19:
            return False
            
        # 3. Consecutividade (max 3 consecutivos)
        consecutivos = 1
        for i in range(1, len(jogo)):
            if jogo[i] == jogo[i-1] + 1:
                consecutivos += 1
                if consecutivos > 3:
                    return False
            else:
                consecutivos = 1
        return True

    def calcular_cobertura_matematica(self, jogos, pool, num_simulacoes=2000):
        """
        Calcula de forma honesta e puramente matemática as probabilidades de acerto
        usando simulações de Monte Carlo baseadas nas regras reais da Lotomania.
        
        1. Cenário Geral (Realidade): 20 dezenas são sorteadas de forma totalmente aleatória entre 0 e 99.
        2. Cenário Condicional (Fidelidade do Pool): 20 dezenas sorteadas estão 100% contidas no pool de 80 dezenas selecionado.
        """
        import random
        
        jogos_sets = [set(jogo) for jogo in jogos]
        pool_set = set(pool)
        
        acertos_geral = {15: 0, 16: 0, 17: 0, 18: 0, 19: 0, 20: 0, 0: 0}
        acertos_cond = {15: 0, 16: 0, 17: 0, 18: 0, 19: 0, 20: 0, 0: 0}
        
        # Simulação 1: Geral (20 dezenas sorteadas de 0 a 99)
        for _ in range(num_simulacoes):
            sorteio = set(random.sample(range(100), 20))
            max_hits = 0
            for jg in jogos_sets:
                hits = len(jg.intersection(sorteio))
                if hits > max_hits:
                    max_hits = hits
            # Registrar todos os níveis alcançados
            for k in acertos_geral.keys():
                if k == 0:
                    if max_hits == 0:
                        acertos_geral[0] += 1
                else:
                    if max_hits >= k:
                        acertos_geral[k] += 1
                        
        # Simulação 2: Condicional (20 dezenas sorteadas estritamente de dentro do pool de 80)
        if len(pool) >= 20:
            for _ in range(num_simulacoes):
                sorteio = set(random.sample(pool, 20))
                max_hits = 0
                for jg in jogos_sets:
                    hits = len(jg.intersection(sorteio))
                    if hits > max_hits:
                        max_hits = hits
                for k in acertos_cond.keys():
                    if k == 0:
                        if max_hits == 0:
                            acertos_cond[0] += 1
                    else:
                        if max_hits >= k:
                            acertos_cond[k] += 1
                            
        # Converter para porcentagem
        prob_geral = {k: round((v / num_simulacoes) * 100, 2) for k, v in acertos_geral.items()}
        prob_cond = {k: round((v / num_simulacoes) * 100, 2) for k, v in acertos_cond.items()}
        
        return {
            "geral": prob_geral,
            "condicional": prob_cond
        }

    def gerar_jogos_cobertura_ia(self, historico, pool_selecionado, quantidade_jogos):
        """
        Gera os jogos de cobertura IA adaptado dinamicamente para a quantidade de jogos solicitada,
        para todas as loterias (incluindo Lotomania com afunilamento de estágios).
        """
        if "lotomania" in self.nome_loteria:
            from motor_cascata import MotorCascata
            motor_c = MotorCascata(pool=pool_selecionado, historico=historico, is_sniper=False)
            res = motor_c.gerar_jogos(quantidade_jogos)
            cobertura_stats = motor_c.calcular_probabilidade(res["jogos"])
            return res["jogos"], res["grupos"], res["tamanho_grupo"], cobertura_stats

        frequencias = self._calcular_frequencias(historico)
        coocorrencia = self._calcular_coocorrencia(historico)
        
        pool = list(pool_selecionado)
        params = self._obter_params_cobertura_dinamico(quantidade_jogos)
        alvo_pool = params["total_pool"]
            
        if len(pool) < alvo_pool:
            ordenados_por_freq = sorted(self.pool, key=lambda n: frequencias.get(n, 0), reverse=True)
            for n in ordenados_por_freq:
                if n not in pool:
                    pool.append(n)
                if len(pool) == alvo_pool:
                    break
        elif len(pool) > alvo_pool:
            pool = sorted(pool, key=lambda n: frequencias.get(n, 0), reverse=True)[:alvo_pool]
            
        pool = sorted(pool)

        if "lotomania" in self.nome_loteria:
            # LÓGICA DE AFUNILAMENTO SEQUENCIAL (ESTÁGIOS) PARA LOTOMANIA
            jogos_finais = []
            grupos_retorno = []
            tamanho_grupo_retorno = 20
            
            # --- ESTÁGIO 1: Grupos de 20 (Até 24 jogos) ---
            if len(jogos_finais) < quantidade_jogos:
                tamanho_grupo_retorno = 20
                grupos_20 = self.dividir_em_grupos_inteligentes(pool, 20, coocorrencia, historico)
                grupos_20 = grupos_20[:4] # Garantir 4 grupos
                grupos_retorno = grupos_20
                
                # Cada grupo de 20 é dividido em duas metades de 10
                metades_10 = {}
                for idx, g in enumerate(grupos_20):
                    metades_10[idx] = (g[:10], g[10:])
                    
                # Gerar combinações de 2 grupos inteiros (40 dezenas) + 10 dezenas de outro
                candidatos_estagio1 = []
                for idx_a, idx_b in itertools.combinations(range(4), 2):
                    g_a = grupos_20[idx_a]
                    g_b = grupos_20[idx_b]
                    outros = [i for i in range(4) if i != idx_a and i != idx_b]
                    
                    for idx_outro in outros:
                        for metade in (0, 1):
                            m_c = metades_10[idx_outro][metade]
                            jogo = sorted(g_a + g_b + m_c)
                            if self._jogo_valido(jogo):
                                score = sum(frequencias.get(n, 0) for n in jogo)
                                candidatos_estagio1.append((jogo, score))
                                
                candidatos_estagio1.sort(key=lambda x: x[1], reverse=True)
                for jg, _ in candidatos_estagio1:
                    if len(jogos_finais) < quantidade_jogos:
                        if jg not in jogos_finais:
                            jogos_finais.append(jg)
                            
            # --- ESTÁGIO 2: Grupos de 10 (Mais 56 jogos, total 80) ---
            if len(jogos_finais) < quantidade_jogos:
                tamanho_grupo_retorno = 10
                grupos_10 = self.dividir_em_grupos_inteligentes(pool, 10, coocorrencia, historico)
                grupos_10 = grupos_10[:8] # Garantir 8 grupos
                grupos_retorno = grupos_10
                
                candidatos_estagio2 = []
                for combo in itertools.combinations(grupos_10, 5):
                    jogo = []
                    for g in combo:
                        jogo.extend(g)
                    jogo = sorted(jogo)
                    if self._jogo_valido(jogo):
                        score = sum(frequencias.get(n, 0) for n in jogo)
                        candidatos_estagio2.append((jogo, score))
                        
                candidatos_estagio2.sort(key=lambda x: x[1], reverse=True)
                for jg, _ in candidatos_estagio2:
                    if len(jogos_finais) < quantidade_jogos:
                        if jg not in jogos_finais:
                            jogos_finais.append(jg)
                            
            # --- ESTÁGIO 3: Grupos de 5 (Mais jogos, total 8088) ---
            if len(jogos_finais) < quantidade_jogos:
                tamanho_grupo_retorno = 5
                grupos_5 = self.dividir_em_grupos_inteligentes(pool, 5, coocorrencia, historico)
                grupos_5 = grupos_5[:16] # Garantir 16 grupos
                grupos_retorno = grupos_5
                
                candidatos_estagio3 = []
                for combo in itertools.combinations(grupos_5, 10):
                    jogo = []
                    for g in combo:
                        jogo.extend(g)
                    jogo = sorted(jogo)
                    if self._jogo_valido(jogo):
                        score = sum(frequencias.get(n, 0) for n in jogo)
                        candidatos_estagio3.append((jogo, score))
                        if len(candidatos_estagio3) >= max(2000, quantidade_jogos * 2):
                            break
                            
                candidatos_estagio3.sort(key=lambda x: x[1], reverse=True)
                for jg, _ in candidatos_estagio3:
                    if len(jogos_finais) < quantidade_jogos:
                        if jg not in jogos_finais:
                            jogos_finais.append(jg)
                            
            # --- ESTÁGIO 4: Grupos de 2 ---
            if len(jogos_finais) < quantidade_jogos:
                tamanho_grupo_retorno = 2
                grupos_2 = self.dividir_em_grupos_inteligentes(pool, 2, coocorrencia, historico)
                grupos_2 = grupos_2[:40]
                grupos_retorno = grupos_2
                
                candidatos_estagio4 = []
                limite_candidatos = max(2000, quantidade_jogos * 2)
                def backtrack(start_idx, combo_indices, dezenas_atuais):
                    if len(combo_indices) == 25:
                        jogo = sorted(dezenas_atuais)
                        if self._jogo_valido(jogo):
                            score = sum(frequencias.get(n, 0) for n in jogo)
                            candidatos_estagio4.append((jogo, score))
                        return
                    for i in range(start_idx, len(grupos_2)):
                        if len(combo_indices) + (len(grupos_2) - i) < 25:
                            return
                        backtrack(i + 1, combo_indices + [i], dezenas_atuais + grupos_2[i])
                        if len(candidatos_estagio4) >= limite_candidatos:
                            return
                backtrack(0, [], [])
                
                candidatos_estagio4.sort(key=lambda x: x[1], reverse=True)
                for jg, _ in candidatos_estagio4:
                    if len(jogos_finais) < quantidade_jogos:
                        if jg not in jogos_finais:
                            jogos_finais.append(jg)
                            
            # --- PREENCHIMENTO DE SEGURANÇA (Se não obteve a quantidade solicitada de jogos válidos) ---
            if len(jogos_finais) < quantidade_jogos:
                import random
                tentativas_preenchimento = 0
                while len(jogos_finais) < quantidade_jogos and tentativas_preenchimento < 1000:
                    tentativas_preenchimento += 1
                    jogo_cand = []
                    disponiveis = list(pool)
                    random.shuffle(disponiveis)
                    
                    # Constrói o jogo dezena por dezena validando as restrições
                    for n in disponiveis:
                        if len(jogo_cand) >= 50:
                            break
                        temp = sorted(jogo_cand + [n])
                        
                        # Valida consecutividade (máximo 3)
                        consecutivos = 1
                        ok = True
                        for idx in range(1, len(temp)):
                            if temp[idx] == temp[idx-1] + 1:
                                consecutivos += 1
                                if consecutivos > 3:
                                    ok = False
                                    break
                            else:
                                consecutivos = 1
                        if not ok:
                            continue
                            
                        # Valida paridade (máximo 27)
                        evens = len([x for x in temp if x % 2 == 0])
                        odds = len(temp) - evens
                        if evens > 27 or odds > 27:
                            continue
                            
                        # Valida zoneamento espacial (máximo 19)
                        d1 = len([x for x in temp if x in self.d1])
                        d2 = len([x for x in temp if x in self.d2])
                        d3 = len([x for x in temp if x in self.d3])
                        if d1 > 19 or d2 > 19 or d3 > 19:
                            continue
                            
                        jogo_cand.append(n)
                        
                    if len(jogo_cand) == 50:
                        jogo_valido = sorted(jogo_cand)
                        if jogo_valido not in jogos_finais:
                            jogos_finais.append(jogo_valido)
                            
            cobertura_stats = self.calcular_cobertura_matematica(jogos_finais, pool)
            return jogos_finais, [sorted(g) for g in grupos_retorno], tamanho_grupo_retorno, cobertura_stats
            
        else:
            # Outras Loterias (Padrão)
            params = self._obter_params_cobertura_dinamico(quantidade_jogos)
            tam_grupo = params["tamanho_grupo"]
            qtd_grupos = params["qtd_grupos"]
            combinar = params["combinar"]
            alvo_pool = params["total_pool"]
            
            grupos = self.dividir_em_grupos_coocorrencia(pool, tam_grupo, coocorrencia)
            grupos = grupos[:qtd_grupos]
            
            grupos_scores = []
            for g in grupos:
                score = sum(frequencias.get(n, 0) for n in g)
                grupos_scores.append((g, score))
            
            grupos_scores.sort(key=lambda x: x[1], reverse=True)
            grupos_ordenados = [x[0] for x in grupos_scores]
            
            jogos_candidatos = []
            limite_candidatos = max(2000, quantidade_jogos * 2)
            
            def backtrack(start_idx, combo_atual, dezenas_atuais):
                if len(combo_atual) == combinar:
                    jogo = sorted(dezenas_atuais)
                    if not self._tem_sequencia_maior_que_tres(jogo):
                        score = sum(frequencias.get(n, 0) for n in jogo)
                        jogos_candidatos.append((jogo, score))
                    return
                
                for i in range(start_idx, len(grupos_ordenados)):
                    if len(combo_atual) + (len(grupos_ordenados) - i) < combinar:
                        return
                        
                    novas_dezenas = dezenas_atuais + grupos_ordenados[i]
                    if self._tem_sequencia_maior_que_tres(sorted(novas_dezenas)):
                        continue
                        
                    backtrack(i + 1, combo_atual + [i], novas_dezenas)
                    if len(jogos_candidatos) >= limite_candidatos:
                        return

            backtrack(0, [], [])
            
            jogos_candidatos.sort(key=lambda x: x[1], reverse=True)
            jogos_finais = [x[0] for x in jogos_candidatos[:quantidade_jogos]]
            cobertura_stats = self.calcular_cobertura_matematica(jogos_finais, pool)
            return jogos_finais, [sorted(g) for g in grupos_ordenados], tam_grupo, cobertura_stats

    def _tem_sequencia_maior_que_tres(self, jogo):
        """Verifica se há mais de 3 números consecutivos em sequência."""
        consecutivos = 1
        for i in range(1, len(jogo)):
            if jogo[i] == jogo[i-1] + 1:
                consecutivos += 1
                if consecutivos > 3:
                    return True
            else:
                consecutivos = 1
        return False

# === GERAÇÃO DO RELATÓRIO MÚLTIPLO DE SAÍDA ===
if __name__ == "__main__":
    # Exemplo genérico de histórico
    historico_exemplo = [
        [5, 12, 15, 30, 45, 50],
        [2, 12, 22, 50, 51, 60],
        [1, 5, 12, 22, 33, 50],
        [10, 11, 50, 51, 55, 59],
        [5, 12, 20, 30, 51, 60]
    ]

    print("=== TESTE DO MOTOR EM MÚLTIPLAS LOTERIAS B2B ===\n")

    # Teste 1: MEGA-SENA
    motor_mega = MotorSugestaoLoteria(nome_loteria="Mega-Sena")
    sugestao_mega, _, _ = motor_mega.gerar_sugestao(historico_exemplo, quantidade_sugestao=30)
    print("LOTERIA: MEGA-SENA")
    print(f"Regra Ativa: Evitar > 3 números consecutivos.")
    print(f"Sugestão (30 números do Pool de 60): {sugestao_mega}\n")

    # Teste 2: LOTOFÁCIL
    motor_loto = MotorSugestaoLoteria(nome_loteria="Lotofácil")
    # Histórico mockado adaptado para o pool da Lotofácil (1 a 25)
    historico_loto = [[1,2,3,4,10,15], [1,2,3,4,10,12]] 
    sugestao_loto, _, _ = motor_loto.gerar_sugestao(historico_loto, quantidade_sugestao=15)
    print("LOTERIA: LOTOFÁCIL")
    print(f"Regra Ativa: Exceção aplicada. Ignorando regra de sequência pela alta densidade.")
    print(f"Sugestão (15 números do Pool de 25): {sugestao_loto}\n")
