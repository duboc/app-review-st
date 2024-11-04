## Prompts de Exemplo

## Prompt 1: Análise Geral do Sentimento (Expandido)

```
Analise o sentimento das reviews de usuários no arquivo CSV, que contém as colunas content, score e o thumbs up do review.

1. Classifique cada review como "Positiva", "Negativa" ou "Neutra" com base no conteúdo textual, considerando que o 'score' pode não refletir com precisão o sentimento expresso.
2. Forneça uma estimativa qualitativa da distribuição percentual de cada categoria de sentimento para ter uma visão geral da opinião dos usuários sobre o aplicativo. 
3. Identifique os principais temas e palavras-chave associados a cada categoria de sentimento, como funcionalidades elogiadas ou criticadas, problemas relatados e sugestões de melhoria.
4. Apresente um resumo conciso da análise, destacando os pontos mais relevantes e as tendências gerais de sentimento.
```

## Prompt 2: Análise Detalhada com Exemplos (Expandido)

```
Realize uma análise aprofundada do sentimento das reviews no arquivo CSV, que contém as colunas content, score e at. 

1. Classifique cada review como "Positiva", "Negativa" ou "Neutra", considerando que o 'score' pode não ser totalmente preciso.
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
4. Se possível, utilize a coluna 'at' para identificar tendências e verificar se certos problemas persistem ao longo do tempo ou se novas sugestões surgiram recentemente.
```

## 

## Prompt 4: Identificação de Fatores que Influenciam o Sentimento

```
Explore o arquivo CSV para identificar fatores que influenciam o sentimento dos usuários.

1. Classifique cada review como "Positiva", "Negativa" ou "Neutra".
2. Investigue se o tipo de dispositivo ('device') ou o país do usuário ('androidVersion') estão relacionados a diferenças no sentimento geral.
3. Analise se certas funcionalidades ou problemas são mais mencionados em reviews de determinados dispositivos ou países.
4. Apresente os resultados de forma clara, mostrando se existem tendências significativas e oferecendo insights sobre como adaptar o aplicativo para diferentes públicos.
```

## Prompt 5: Detecção de Reviews Inconsistentes ou Spam

```
Utilize técnicas de análise de sentimento e linguagem para identificar possíveis reviews falsas ou spam no arquivo CSV que contém a coluna content.

1. Analise o sentimento de cada review e verifique se há discrepâncias entre o sentimento expresso e o 'rating' atribuído, o que pode indicar uma review falsa.
2. Identifique padrões de linguagem suspeitos, como repetição excessiva de palavras-chave, frases genéricas ou estruturas gramaticais incomuns.
3. Verifique se há reviews muito similares ou idênticas, o que pode sugerir spam ou manipulação de avaliações.
4. Apresente uma lista de reviews potencialmente falsas ou spam, juntamente com os critérios utilizados para identificá-las.
```

## Prompt 6: Comparação de Sentimento entre Versões do Aplicativo

###  **Selecione o modelo `Gemini-1.5-Pro-002` e altere a temperatura para `0,3`.**

### **Utilize este System Instruction:**

````
# Análise de Sentimento de Reviews de App
## Objetivo
Você é um sistema de IA Generativa responsável por analisar o sentimento de reviews de um aplicativo de celular na Google Play, gerando um JSON com os resultados.

## Formato de Entrada
Uma lista de reviews de aplicativos da Google Play, onde cada review inclui a versão do aplicativo (reviewCreatedVersion) e o texto da review.

## Formato de Saída
Um JSON no seguinte formato:
```json
{
  "historico_versoes": [
    {
      "versao_aplicativo": "string",
      "resumo_sentimento": "string",
      "sentimento": "positivo" | "negativo" | "neutro",
      "score_sentimento": "integer" 
    },
    ...
  ],
  "melhor_sentimento": {
    "versao_aplicativo": "string",
    "resumo_sentimento": "string"
  },
  "pior_sentimento": {
    "versao_aplicativo": "string",
    "resumo_sentimento": "string"
  }
}
```

## Instruções para a análise

### Analise as últimas 5 versões do aplicativo
1. Identifique as últimas 5 versões do aplicativo com base na coluna reviewCreatedVersion.
2. Ordene as versões em ordem decrescente (da mais recente para a mais antiga).
3. Para cada versão:
- Classificar o sentimento geral das reviews:
- Analise o texto de cada review associada à versão.
- Agregue os sentimentos individuais de cada review para determinar o sentimento geral da versão como positivo, negativo ou neutro.

Utilize a seguinte lógica para determinar o sentimento geral:
- Se a maioria das reviews for positiva, classifique a versão como positivo.
- Se a maioria das reviews for negativa, classifique a versão como negativo.
- Se houver um equilíbrio entre reviews positivas e negativas, ou se a maioria for neutra, classifique a versão como neutro.

4. Calcular o score de sentimento
Com base na análise das reviews, atribua um score (valores inteir) de 1 a 10 para representar a positividade do sentimento em relação à versão.

Utilize a seguinte escala como referência:
* 1-3: Sentimento muito negativo
* 4-6: Sentimento negativo a neutro
* 7-8: Sentimento positivo
* 9-10: Sentimento muito positivo

5. Gere um resumo do sentimento: Crie um resumo conciso (máximo de 100 palavras) que descreva o sentimento geral da versão. Inclua informações sobre os principais aspectos que geraram reações positivas ou negativas.

### Identifique a melhor e a pior versão
Com base na análise de sentimento das últimas 5 versões do aplicativo, identifique dentre estas 5 versões qual teve o sentimento mais positivo e qual teve o sentimento mais negativo.

## Exemplo da saída
```json
{
  "historico_versoes": [
    {
      "versao_aplicativo": "2.0.0",
      "resumo_sentimento": "Sentimento geral positivo, com usuários elogiando a nova interface e a performance aprimorada...",
      "sentimento": "positivo",
      "score_sentimento": 8
    },
    {
      "versao_aplicativo": "1.5.0",
      "resumo_sentimento": "Sentimento misto, com alguns usuários relatando bugs e problemas de estabilidade.",
      "sentimento": "neutro",
      "score_sentimento": 5
    },
    ...
  ],
  "melhor_sentimento": {
    "versao_aplicativo": "2.0.0",
    "resumo_sentimento": "Sentimento geral positivo, com usuários elogiando a nova interface...",
  },
  "pior_sentimento": {
    "versao_aplicativo": "1.2.0",
    "resumo_sentimento": "Sentimento negativo, com muitos usuários reclamando de crashes e perda de dados."
  }
}
```

## Considerações Adicionais
- Utilize todo seu conhecimento sobre Customer Experience, Google Play Store store e análise de sentimento para realizar a análise.
- Priorize a precisão e a objetividade na classificação do sentimento e na geração dos resumos.
- O score para cada versão do aplicativo deve ser um valor inteiro entre 1 e 10.

````

### **Configure a saída para respeitar este JSON schema:** 

```
{
  "type": "object",
  "properties": {
    "historico_versoes": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "versao_aplicativo": {
            "type": "string"
          },
          "resumo_sentimento": {
            "type": "string"
          },
          "sentimento": {
            "type": "string",
            "enum": [
              "positivo",
              "negativo",
              "neutro"
            ]
          },
          "score_sentimento_positivo": {
            "type": "integer"
          }
        },
        "required": [
          "versao_aplicativo",
          "resumo_sentimento",
          "sentimento",
          "score_sentimento_positivo"
        ]
      }
    },
    "melhor_sentimento": {
      "type": "object",
      "properties": {
        "versao_aplicativo": {
          "type": "string"
        },
        "resumo_sentimento": {
          "type": "string"
        }
      },
      "required": [
        "versao_aplicativo",
        "resumo_sentimento"
      ]
    },
    "pior_sentimento": {
      "type": "object",
      "properties": {
        "versao_aplicativo": {
          "type": "string"
        },
        "resumo_sentimento": {
          "type": "string"
        }
      },
      "required": [
        "versao_aplicativo",
        "resumo_sentimento"
      ]
    }
  },
  "required": [
    "historico_versoes",
    "melhor_sentimento",
    "pior_sentimento"
  ]
}

```

### **No User Prompt, adicione como anexo o CSV baixado, juntamente com este texto abaixo:**

```
Analise as reviews deste aplicativo.
```

## 

## Prompt 7: Extraindo Insights de Reviews para Análise de Jogabilidade a Partir de Vídeo

1. ### Caso você seja uma empresa de gaming, preferencialmente crie uma gravação de seu jogo para uso nesse exercício ou baixe o vídeo do jogo na aba **Artifacts**.

2. ### Baixe o CSV com os reviews de sua aplicação correspondente ao vídeo ou use o ID **org.supertuxkart.stk** para baixar os reviews correspondentes ao vídeo baixado no link acima.

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

