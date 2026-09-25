# Resumo da Análise de Composição do Universo de Investimento

Este documento sumariza os resultados e as tabelas geradas no notebook `universe_composition_analysis.ipynb`, que avalia a estrutura do universo de ativos e os extremos de cada portfólio.

## 1. Distribuição Global de Tipos de Ativos
O universo de investimento contém um total de **40.662 registros** ao longo dos anos, divididos em grandes grupos (ações e não-ações). A grande maioria é composta por ações individuais, seguidas pelos ETFs.

**Total Histórico (Contagem Absoluta):**
- **Stock (Ações):** 24.004
- **ETF:** 11.981
- **Closed-End Fund:** 3.200
- **REIT (Fundo Imobiliário):** 1.477

---

## 2. Ações vs Não-Ações (Evolução Temporal)
A análise temporal revela como a composição do mercado e da amostra tem se alterado ao longo da última década.

**Explicação Breve:**
Existe uma clara **tendência de crescimento na proporção de Não-Ações** (principalmente ETFs) por quantidade. Em 2014, o universo era composto por 65% de Ações e 35% de Não-Ações. Em 2024, essa proporção mudou para **55% Ações e 45% Não-Ações**. Por Market Cap, ações dominavam com >80% até 2018. **Atenção:** As tabelas indicam que, de 2019 em diante, as ações passam a representar subitamente mais de ~99% do Market Cap total. Isso sugere fortemente uma mudança na metodologia da base de dados de origem (market cap de fundos pode estar ausente).

### 2.1 Por Quantidade (Count %)
|   year | Non-Stock   | Stock   |
|-------:|:------------|:--------|
|   2014 | 35.00%      | 65.00%  |
|   2015 | 36.67%      | 63.33%  |
|   2016 | 38.24%      | 61.76%  |
|   2017 | 39.03%      | 60.97%  |
|   2018 | 40.12%      | 59.88%  |
|   2019 | 40.42%      | 59.58%  |
|   2020 | 41.24%      | 58.76%  |
|   2021 | 42.24%      | 57.76%  |
|   2022 | 43.19%      | 56.81%  |
|   2023 | 43.94%      | 56.06%  |
|   2024 | 44.77%      | 55.23%  |

### 2.2 Por Market Cap (Mcap %)
|   year | Non-Stock   | Stock   |
|-------:|:------------|:--------|
|   2014 | 18.20%      | 81.80%  |
|   2015 | 17.34%      | 82.66%  |
|   2016 | 18.89%      | 81.11%  |
|   2017 | 18.76%      | 81.24%  |
|   2018 | 19.06%      | 80.94%  |
|   2019 | 0.87%       | 99.13%  |
|   2020 | 1.00%       | 99.00%  |
|   2021 | 0.96%       | 99.04%  |
|   2022 | 0.70%       | 99.30%  |
|   2023 | 0.82%       | 99.18%  |
|   2024 | 0.80%       | 99.20%  |

---

## 3. Composição Detalhada dos "Não-Ações"

**Explicação Breve:**
Quando isolamos apenas o grupo de Não-Ações (ETFs, CEFs e REITs), observamos que **os ETFs dominam**, saltando de **63%** do universo de Não-Ações em 2014 para **78%** em 2024. Em contrapartida, os **Closed-End Funds (CEFs)** caíram de **26% para 14,5%**, e os **REITs** de ~10% para 7,4%. Os ETFs também lideram com folga a distribuição de Market Cap deste segmento.

### 3.1 Detalhe de Não-Ações por Quantidade
|   year | Closed-End Fund   | ETF    | REIT   |
|-------:|:------------------|:-------|:-------|
|   2014 | 26.23%            | 63.06% | 10.70% |
|   2015 | 24.37%            | 65.48% | 10.16% |
|   2016 | 23.15%            | 67.13% | 9.72%  |
|   2017 | 22.51%            | 68.34% | 9.15%  |
|   2018 | 21.48%            | 69.03% | 9.50%  |
|   2019 | 20.39%            | 70.43% | 9.18%  |
|   2020 | 19.04%            | 71.78% | 9.18%  |
|   2021 | 17.87%            | 73.48% | 8.64%  |
|   2022 | 16.51%            | 75.12% | 8.36%  |
|   2023 | 15.32%            | 76.73% | 7.95%  |
|   2024 | 14.51%            | 78.05% | 7.44%  |

### 3.2 Detalhe de Não-Ações por Market Cap
|   year | Closed-End Fund   | ETF    | REIT   |
|-------:|:------------------|:-------|:-------|
|   2014 | 8.50%             | 76.67% | 14.83% |
|   2015 | 4.13%             | 78.61% | 17.25% |
|   2016 | 3.69%             | 80.78% | 15.52% |
|   2017 | 3.35%             | 82.40% | 14.25% |
|   2018 | 2.98%             | 82.56% | 14.46% |
|   2019 | 2.59%             | 82.74% | 14.67% |
|   2020 | 2.61%             | 84.65% | 12.74% |
|   2021 | 2.15%             | 82.55% | 15.30% |
|   2022 | 2.09%             | 83.91% | 14.00% |
|   2023 | 1.66%             | 85.06% | 13.28% |
|   2024 | 1.54%             | 87.14% | 11.32% |

---

## 4. Composição Setorial das Ações

**Explicação Breve:**
Analisando apenas as "Stocks", o setor **Financeiro** lidera a quantidade de empresas (representando historicamente em torno de ~20% a 21%), seguido por **Industrials** (~15 a 17%) e **Healthcare** (crescendo de 13% para mais de 19%). Por Market Cap, os dados reforçam a anomalia pós-2019, onde o setor **Financeiro aparece concentrando de 95% a 97% do Market Cap**, indicando que valores de Market Cap para outros setores estão ausentes na fonte.

### 4.1 Ações por Setor (Quantidade %)
|   year | Basic Materials   | Communication Services   | Consumer Cyclical   | Consumer Defensive   | Energy   | Financial   | Healthcare   | Industrials   | Real Estate   | Technology   | Utilities   |
|-------:|:------------------|:-------------------------|:--------------------|:---------------------|:---------|:------------|:-------------|:--------------|:--------------|:-------------|:------------|
|   2014 | 4.92%             | 3.33%                    | 12.32%              | 5.37%                | 4.97%    | 21.02%      | 12.99%       | 17.29%        | 0.96%         | 13.50%       | 3.33%       |
|   2015 | 4.90%             | 3.32%                    | 12.36%              | 5.28%                | 4.90%    | 21.13%      | 13.07%       | 17.10%        | 0.98%         | 13.73%       | 3.21%       |
|   2016 | 5.01%             | 3.46%                    | 12.25%              | 5.27%                | 5.17%    | 21.10%      | 13.16%       | 16.94%        | 0.96%         | 13.48%       | 3.20%       |
|   2017 | 4.79%             | 3.56%                    | 12.07%              | 5.19%                | 5.60%    | 20.98%      | 13.54%       | 16.70%        | 0.92%         | 13.59%       | 3.05%       |
|   2018 | 4.70%             | 3.67%                    | 12.24%              | 5.14%                | 5.68%    | 20.70%      | 14.19%       | 16.30%        | 0.98%         | 13.46%       | 2.94%       |
|   2019 | 4.61%             | 3.74%                    | 12.08%              | 4.89%                | 5.44%    | 20.57%      | 15.36%       | 15.96%        | 0.97%         | 13.51%       | 2.86%       |
|   2020 | 4.50%             | 3.88%                    | 11.91%              | 4.85%                | 5.29%    | 20.25%      | 16.28%       | 15.62%        | 1.01%         | 13.63%       | 2.78%       |
|   2021 | 4.49%             | 3.93%                    | 11.79%              | 4.87%                | 5.30%    | 19.91%      | 16.79%       | 15.38%        | 0.98%         | 13.80%       | 2.78%       |
|   2022 | 4.44%             | 4.04%                    | 11.78%              | 4.81%                | 5.50%    | 19.65%      | 17.28%       | 15.08%        | 1.02%         | 13.74%       | 2.65%       |
|   2023 | 4.26%             | 4.11%                    | 11.54%              | 4.69%                | 5.50%    | 19.40%      | 18.40%       | 14.79%        | 1.08%         | 13.71%       | 2.52%       |
|   2024 | 4.14%             | 4.14%                    | 11.51%              | 4.77%                | 5.33%    | 19.24%      | 19.13%       | 14.35%        | 1.04%         | 13.95%       | 2.40%       |

### 4.2 Ações por Setor (Market Cap %)
|   year | Basic Materials   | Communication Services   | Consumer Cyclical   | Consumer Defensive   | Energy   | Financial   | Healthcare   | Industrials   | Real Estate   | Technology   | Utilities   |
|-------:|:------------------|:-------------------------|:--------------------|:---------------------|:---------|:------------|:-------------|:--------------|:--------------|:-------------|:------------|
|   2014 | 1.92%             | 19.47%                   | 8.21%               | 8.78%                | 6.73%    | 17.31%      | 12.37%       | 9.18%         | 0.14%         | 12.91%       | 2.98%       |
|   2015 | 1.79%             | 18.06%                   | 10.58%              | 9.24%                | 5.25%    | 17.49%      | 12.70%       | 8.79%         | 0.17%         | 12.97%       | 2.95%       |
|   2016 | 2.08%             | 15.47%                   | 9.72%               | 9.38%                | 6.51%    | 18.87%      | 11.21%       | 9.64%         | 0.14%         | 13.85%       | 3.13%       |
|   2017 | 2.14%             | 15.34%                   | 9.90%               | 9.36%                | 5.98%    | 18.48%      | 10.92%       | 9.63%         | 0.16%         | 15.27%       | 2.81%       |
|   2018 | 1.81%             | 17.40%                   | 10.20%              | 8.81%                | 5.30%    | 16.91%      | 12.76%       | 8.29%         | 0.17%         | 15.30%       | 3.05%       |
|   2019 | 0.07%             | 0.55%                    | 0.39%               | 0.30%                | 0.17%    | 96.91%      | 0.47%        | 0.32%         | 0.01%         | 0.69%        | 0.12%       |
|   2020 | 0.09%             | 1.23%                    | 0.64%               | 0.36%                | 0.12%    | 95.45%      | 0.57%        | 0.37%         | 0.01%         | 1.04%        | 0.12%       |
|   2021 | 0.09%             | 0.89%                    | 0.60%               | 0.34%                | 0.15%    | 95.75%      | 0.55%        | 0.36%         | 0.01%         | 1.14%        | 0.11%       |
|   2022 | 0.07%             | 0.42%                    | 0.31%               | 0.29%                | 0.18%    | 97.15%      | 0.47%        | 0.28%         | 0.01%         | 0.71%        | 0.11%       |
|   2023 | 0.07%             | 0.51%                    | 0.44%               | 0.24%                | 0.16%    | 96.64%      | 0.46%        | 0.33%         | 0.01%         | 1.06%        | 0.09%       |
|   2024 | 0.06%             | 0.53%                    | 0.46%               | 0.22%                | 0.14%    | 96.68%      | 0.37%        | 0.29%         | 0.01%         | 1.16%        | 0.08%       |

---

## 5. Composição de Portfólios Extremos (Decil 1 vs Decil 10)

A análise buscou entender a característica estrutural dos ativos que compõem o **Decil 1 (Portfólio Central)** e o **Decil 10 (Portfólio Periférico)** das duas principais topologias de rede investigadas: **HCM** e **Pozzi**.

### 5.1 Topologia HCM (Ações vs Não-Ações)

**Explicação Breve:**
O núcleo do HCM (Decil 1) abriga a maior parte das Ações puras (~55-75% nos primeiros anos, embora haja flutuação). Interessante notar que na periferia (Decil 10), existe uma predominância frequente de Não-Ações (acima de 50% em muitos anos).

#### Decil 1 (Núcleo)
|   year | Non-Stock   | Stock   |
|-------:|:------------|:--------|
|   2014 | 24.91%      | 75.09%  |
|   2015 | 26.21%      | 73.79%  |
|   2016 | 36.18%      | 63.82%  |
|   2017 | 61.92%      | 38.08%  |
|   2018 | 38.89%      | 61.11%  |
|   2019 | 32.69%      | 67.31%  |
|   2020 | 61.14%      | 38.86%  |
|   2021 | 58.13%      | 41.87%  |
|   2022 | 64.35%      | 35.65%  |
|   2023 | 64.21%      | 35.79%  |
|   2024 | 55.10%      | 44.90%  |
#### Decil 10 (Periferia)
|   year | Non-Stock   | Stock   |
|-------:|:------------|:--------|
|   2014 | 54.58%      | 45.42%  |
|   2015 | 32.41%      | 67.59%  |
|   2016 | 46.05%      | 53.95%  |
|   2017 | 54.97%      | 45.03%  |
|   2018 | 55.56%      | 44.44%  |
|   2019 | 51.37%      | 48.63%  |
|   2020 | 59.07%      | 40.93%  |
|   2021 | 58.13%      | 41.87%  |
|   2022 | 56.48%      | 43.52%  |
|   2023 | 49.24%      | 50.76%  |
|   2024 | 61.22%      | 38.78%  |

### 5.2 Topologia Pozzi (Ações vs Não-Ações)

**Explicação Breve:**
O modelo Pozzi (PMFG) consegue conectar os fundos/ETFs muito mais no núcleo do que o HCM. Seu Decil 1 tem uma alta porcentagem de ETFs, enquanto o seu **Decil 10 joga fortemente as Ações puras para a periferia** (alcançando picos de até 81% de ações na periferia em 2023).

#### Decil 1 (Núcleo)
|   year | Non-Stock   | Stock   |
|-------:|:------------|:--------|
|   2014 | 47.62%      | 52.38%  |
|   2015 | 53.45%      | 46.55%  |
|   2016 | 28.62%      | 71.38%  |
|   2017 | 40.87%      | 59.13%  |
|   2018 | 33.04%      | 66.96%  |
|   2019 | 60.16%      | 39.84%  |
|   2020 | 37.82%      | 62.18%  |
|   2021 | 43.84%      | 56.16%  |
|   2022 | 60.19%      | 39.81%  |
|   2023 | 41.00%      | 59.00%  |
|   2024 | 60.41%      | 39.59%  |
#### Decil 10 (Periferia)
|   year | Non-Stock   | Stock   |
|-------:|:------------|:--------|
|   2014 | 64.47%      | 35.53%  |
|   2015 | 26.21%      | 73.79%  |
|   2016 | 23.36%      | 76.64%  |
|   2017 | 49.69%      | 50.31%  |
|   2018 | 23.39%      | 76.61%  |
|   2019 | 25.00%      | 75.00%  |
|   2020 | 54.15%      | 45.85%  |
|   2021 | 47.04%      | 52.96%  |
|   2022 | 31.25%      | 68.75%  |
|   2023 | 18.87%      | 81.13%  |
|   2024 | 62.45%      | 37.55%  |

### 5.3 Setores nas Ações Extremos (HCM)

**Explicação Breve:**
Olhando apenas para as ações no HCM: o **núcleo (Decil 1)** é dominado por indústrias cíclicas (**Industrials ~30%** e **Financial ~25%**). Por outro lado, a periferia (**Decil 10**) tem um altíssimo desvio para o setor de **Healthcare** (chegando a incríveis 67% em 2023!), além de Financial. O isolamento do setor de Saúde na periferia da rede faz muito sentido econômico devido ao seu comportamento idiossincrático (empresas biológicas e farmacêuticas descoladas do ciclo de mercado).

#### Decil 1 (Núcleo)
|   year | Basic Materials   | Communication Services   | Consumer Cyclical   | Consumer Defensive   | Energy   | Financial   | Healthcare   | Industrials   | Real Estate   | Technology   | Utilities   |
|-------:|:------------------|:-------------------------|:--------------------|:---------------------|:---------|:------------|:-------------|:--------------|:--------------|:-------------|:------------|
|   2014 | 6.83%             | 2.44%                    | 12.68%              | 0.98%                | 0.98%    | 19.51%      | 2.93%        | 37.07%        | 1.46%         | 15.12%       | 0.00%       |
|   2015 | 1.87%             | 3.27%                    | 11.68%              | 0.93%                | 0.47%    | 28.50%      | 6.54%        | 28.50%        | 1.40%         | 16.82%       | 0.00%       |
|   2016 | 4.12%             | 5.67%                    | 14.43%              | 1.55%                | 0.52%    | 27.84%      | 5.15%        | 26.29%        | 1.03%         | 13.40%       | 0.00%       |
|   2017 | 6.50%             | 2.44%                    | 15.45%              | 2.44%                | 3.25%    | 18.70%      | 4.07%        | 24.39%        | 3.25%         | 18.70%       | 0.81%       |
|   2018 | 6.70%             | 2.87%                    | 7.66%               | 0.00%                | 0.96%    | 29.67%      | 5.26%        | 33.97%        | 1.91%         | 11.00%       | 0.00%       |
|   2019 | 4.49%             | 2.86%                    | 7.35%               | 1.22%                | 0.82%    | 41.63%      | 4.49%        | 28.16%        | 0.00%         | 8.98%        | 0.00%       |
|   2020 | 7.33%             | 2.67%                    | 12.00%              | 3.33%                | 0.67%    | 24.67%      | 2.67%        | 32.67%        | 2.00%         | 11.33%       | 0.67%       |
|   2021 | 7.06%             | 2.35%                    | 12.94%              | 1.76%                | 0.59%    | 26.47%      | 4.12%        | 31.76%        | 1.18%         | 11.18%       | 0.59%       |
|   2022 | 9.09%             | 0.65%                    | 14.94%              | 2.60%                | 0.00%    | 20.78%      | 1.95%        | 35.06%        | 1.95%         | 12.34%       | 0.65%       |
|   2023 | 9.09%             | 1.21%                    | 27.27%              | 1.21%                | 0.00%    | 13.33%      | 0.61%        | 34.55%        | 3.64%         | 9.09%        | 0.00%       |
|   2024 | 5.00%             | 3.64%                    | 16.82%              | 0.00%                | 0.00%    | 15.00%      | 4.09%        | 32.27%        | 2.73%         | 20.45%       | 0.00%       |
#### Decil 10 (Periferia)
|   year | Basic Materials   | Communication Services   | Consumer Cyclical   | Consumer Defensive   | Energy   | Financial   | Healthcare   | Industrials   | Real Estate   | Technology   | Utilities   |
|-------:|:------------------|:-------------------------|:--------------------|:---------------------|:---------|:------------|:-------------|:--------------|:--------------|:-------------|:------------|
|   2014 | 6.45%             | 3.23%                    | 3.23%               | 2.42%                | 8.06%    | 33.87%      | 14.52%       | 9.68%         | 1.61%         | 15.32%       | 1.61%       |
|   2015 | 5.61%             | 1.02%                    | 4.08%               | 3.06%                | 5.10%    | 29.08%      | 18.37%       | 10.20%        | 2.04%         | 12.24%       | 9.18%       |
|   2016 | 6.10%             | 2.44%                    | 6.71%               | 3.05%                | 5.49%    | 26.22%      | 14.63%       | 10.37%        | 3.05%         | 7.93%        | 14.02%      |
|   2017 | 3.45%             | 3.45%                    | 9.66%               | 2.07%                | 1.38%    | 25.52%      | 13.10%       | 11.72%        | 2.76%         | 11.03%       | 15.86%      |
|   2018 | 6.58%             | 1.32%                    | 6.58%               | 3.95%                | 3.95%    | 16.45%      | 15.79%       | 11.84%        | 1.97%         | 10.53%       | 21.05%      |
|   2019 | 2.82%             | 1.13%                    | 6.21%               | 3.39%                | 3.95%    | 19.77%      | 17.51%       | 12.43%        | 0.56%         | 10.73%       | 21.47%      |
|   2020 | 4.43%             | 4.43%                    | 9.49%               | 6.96%                | 3.80%    | 26.58%      | 13.29%       | 12.66%        | 2.53%         | 15.19%       | 0.63%       |
|   2021 | 2.35%             | 5.88%                    | 20.59%              | 4.71%                | 5.88%    | 24.71%      | 9.41%        | 12.94%        | 1.76%         | 10.59%       | 1.18%       |
|   2022 | 3.72%             | 1.60%                    | 6.38%               | 5.85%                | 1.60%    | 19.68%      | 43.62%       | 9.04%         | 1.06%         | 6.91%        | 0.53%       |
|   2023 | 2.99%             | 0.85%                    | 1.28%               | 1.28%                | 6.84%    | 7.26%       | 67.09%       | 5.98%         | 0.85%         | 5.13%        | 0.43%       |
|   2024 | 8.95%             | 2.63%                    | 3.16%               | 11.58%               | 10.53%   | 15.79%      | 17.89%       | 11.58%        | 2.11%         | 14.74%       | 1.05%       |
