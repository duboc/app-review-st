## Prompts de Exemplo

## Prompt 1: Análise Geral do Sentimento (Expandido)

```
Analise o sentimento das reviews de usuários no arquivo CSV, que contém as colunas content, score e o thumbs up do review.

1. Classifique cada review como "Positiva", "Negativa" ou "Neutra" com base no conteúdo textual, considerando que o 'rating' pode não refletir com precisão o sentimento expresso.
2. Calcule a distribuição percentual de cada categoria de sentimento para fornecer uma visão geral da opinião dos usuários sobre o aplicativo.
3. Identifique os principais temas e palavras-chave associados a cada categoria de sentimento, como funcionalidades elogiadas ou criticadas, problemas relatados e sugestões de melhoria.
4. Apresente um resumo conciso da análise, destacando os pontos mais relevantes e as tendências gerais de sentimento.
```

## Prompt 2: Análise Detalhada com Exemplos (Expandido)

```
Realize uma análise aprofundada do sentimento das reviews no arquivo CSV, que contém as colunas content, score e at. 

1. Classifique cada review como "Positiva", "Negativa" ou "Neutra", considerando que o 'rating' pode não ser totalmente preciso.
2. Para cada categoria de sentimento:
    * Descreva os principais temas e palavras-chave, agrupando-os por similaridade e relevância.
    * Selecione 3 exemplos de reviews que representem claramente o sentimento da categoria, incluindo a data da review para contextualização.
3. Apresente uma análise geral da distribuição dos sentimentos, mostrando a evolução ao longo do tempo (se houver dados suficientes).
4. Inclua insights sobre possíveis causas de mudanças no sentimento, como atualizações do aplicativo ou eventos externos.
```

## Prompt 3: Foco em Problemas e Sugestões (Expandido)

```
Analise as reviews no arquivo CSV, focando na identificação de problemas e sugestões relatados pelos usuários.

1. Extraia as principais reclamações e problemas mencionados nas reviews negativas, categorizando-os por tipo (bugs, funcionalidades, desempenho, etc.) e frequência.
2. Identifique as sugestões e funcionalidades mais solicitadas pelos usuários, agrupando-as por tema e priorizando as mais frequentes ou impactantes.
3. Apresente um relatório estruturado com os problemas e sugestões, incluindo exemplos de reviews relevantes e destacando os pontos mais críticos que demandam atenção imediata dos desenvolvedores.
4. Se possível, utilize a coluna 'data' para identificar tendências e verificar se certos problemas persistem ao longo do tempo ou se novas sugestões surgiram recentemente.
```

## Prompt 4: Comparação de Sentimento entre Versões do Aplicativo

```
x
```

## Prompt 5: Identificação de Fatores que Influenciam o Sentimento

```
Explore o arquivo CSV que contém as colunas 'review_text', 'rating', 'device_type' e 'user_country', para identificar fatores que influenciam o sentimento dos usuários.

1. Classifique cada review como "Positiva", "Negativa" ou "Neutra".
2. Investigue se o tipo de dispositivo ('device_type') ou o país do usuário ('user_country') estão relacionados a diferenças no sentimento geral.
3. Analise se certas funcionalidades ou problemas são mais mencionados em reviews de determinados dispositivos ou países.
4. Apresente os resultados de forma clara, mostrando se existem tendências significativas e oferecendo insights sobre como adaptar o aplicativo para diferentes públicos.
```

## Prompt 6: Detecção de Reviews Falsas ou Spam

```
Utilize técnicas de análise de sentimento e linguagem para identificar possíveis reviews falsas ou spam no arquivo CSVque contém a coluna content.

1. Analise o sentimento de cada review e verifique se há discrepâncias entre o sentimento expresso e o 'rating' atribuído, o que pode indicar uma review falsa.
2. Identifique padrões de linguagem suspeitos, como repetição excessiva de palavras-chave, frases genéricas ou estruturas gramaticais incomuns.
3. Verifique se há reviews muito similares ou idênticas, o que pode sugerir spam ou manipulação de avaliações.
4. Apresente uma lista de reviews potencialmente falsas ou spam, juntamente com os critérios utilizados para identificá-las.
```

## **Prompt para Extrair Insights de Reviews para Análise de Jogabilidade de Vídeo**

```
Analise o arquivo CSV que contém reviews de usuários sobre um jogo, com o objetivo de identificar pontos de melhoria na jogabilidade que podem ser observados em uma gravação do jogo que também está sendo incluída nessa requisição.

1. Extraia das reviews **negativas e neutras** os principais problemas, críticas e sugestões relacionados à jogabilidade, como:
    * Controles: dificuldades, imprecisões, falta de responsividade.
    * Mecânicas de jogo: complexidade, repetitividade, falta de equilíbrio.
    * Design de níveis: frustração, falta de desafio, bugs.
    * Inteligência artificial: inimigos previsíveis, comportamento inconsistente.
    * Progressão: dificuldade em avançar, falta de recompensas significativas.
    * Outros aspectos da jogabilidade mencionados nas reviews.

2. Organize os problemas e sugestões em categorias, priorizando aqueles mais frequentes ou impactantes.

3. Para cada problema ou sugestão identificado, forneça uma descrição clara e objetiva de como ele pode se manifestar na gravação do jogo. Exemplos:

    * **Problema:** "Controles imprecisos"
        * **Como observar na gravação:** Movimentos do personagem que não correspondem aos comandos do jogador, dificuldade em realizar ações específicas, câmera que atrapalha a visualização.
    * **Sugestão:** "Mais variedade de inimigos"
        * **Como observar na gravação:** Repetição frequente dos mesmos tipos de inimigos, falta de desafio em combates, sensação de monotonia.

4. Inclua exemplos de trechos específicos das reviews que ilustrem cada problema ou sugestão, para facilitar a contextualização durante a análise da gravação.

5. Ao final, apresente um resumo dos principais pontos de atenção na jogabilidade, com base nas reviews, para guiar a análise da gravação e identificar oportunidades de melhoria.
```

