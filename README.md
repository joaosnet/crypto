# Projeto Alternativo: Sistema de Trading Algorítmico com Aprendizado por Reforço para Mercados de Criptomoedas

![GitHub repo size](https://img.shields.io/github/repo-size/joaosnet/crypto?style=for-the-badge)
![GitHub language count](https://img.shields.io/github/languages/count/joaosnet/crypto?style=for-the-badge)
![GitHub forks](https://img.shields.io/github/forks/joaosnet/crypto?style=for-the-badge)
![Bitbucket open issues](https://img.shields.io/bitbucket/issues/joaosnet/crypto?style=for-the-badge)
![Bitbucket open pull requests](https://img.shields.io/bitbucket/pr-raw/joaosnet/crypto?style=for-the-badge)
[![pt-br](https://img.shields.io/badge/lang-pt--br-green.svg)](https://github.com/joaosnet/crypto/blob/master/README.pt-br.md)

## Descrição do Projeto

O mercado de criptomoedas é conhecido por sua alta volatilidade e operação contínua, o que apresenta oportunidades únicas para estratégias automatizadas de trading. Este projeto visa desenvolver um sistema de trading algorítmico que utiliza técnicas de Aprendizado por Reforço (RL) para otimizar decisões de compra e venda de criptomoedas, especificamente Bitcoin, em tempo real.

## Habilidades Desenvolvidas
<img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white" /> <img src="https://img.shields.io/badge/Pandas-150458?style=for-the-badge&logo=pandas&logoColor=white" /> <img src="https://img.shields.io/badge/TA--Lib-3776AB?style=for-the-badge&logo=python&logoColor=white" /> <img src="https://img.shields.io/badge/OpenAI_Gym-232F3E?style=for-the-badge&logo=openai&logoColor=white" /> <img src="https://img.shields.io/badge/Stable_Baselines3-232F3E?style=for-the-badge&logo=openai&logoColor=white" /> <img src="https://img.shields.io/badge/Dash-232F3E?style=for-the-badge&logo=dash&logoColor=white" />

# Tabela de Conteúdos

* [Descrição do Projeto](#descrição-do-projeto)
* [Habilidades Desenvolvidas](#habilidades-desenvolvidas)
* [Objetivos](#objetivos)
    * [Geral](#geral)
    * [Específicos](#específicos)
    * [Ajustes e Melhorias](#ajustes-e-melhorias)
* [🤝 Contribuidores](#-contribuidores)
* [Como Executar](#como-executar)
* [📫 Contribuindo para o Projeto](#-contribuindo-para-o-projeto)

## Objetivos

### Geral

Desenvolver um bot de trading algorítmico modular que:
1. Capture continuamente dados de mercado da API da Bitypreço (exchange).
2. Utilize indicadores técnicos para tomar decisões de compra e venda.
3. Implemente estratégias de Aprendizado por Reforço para otimizar essas decisões.

### Específicos

- **Coleta de Dados**: O bot captura continuamente dados de mercado, como preços, volumes e outros indicadores técnicos, da API da Bitypreço.
- **Análise Técnica**: Utiliza indicadores técnicos como RSI, MACD, Bandas de Bollinger, Estocástico, entre outros, para identificar sinais de compra e venda.
- **Execução de Ordens**: Com base nos sinais gerados, o bot executa ordens de compra e venda de criptomoedas.
- **Aprendizado por Reforço**: Implementa agentes de RL que aprendem e otimizam estratégias de trading com base em dados históricos e em tempo real.
- **Backtesting**: Permite testar diferentes estratégias de trading em dados históricos para avaliar sua eficácia antes de aplicá-las em tempo real.

### Ajustes e Melhorias

O projeto está em desenvolvimento contínuo, e as próximas atualizações focarão nas seguintes tarefas:

- [x] Coleta de Dados
- [x] Análise Técnica
- [x] Execução de Ordens
- [x] Aprendizado por Reforço
- [x] Backtesting
- [ ] Integração com outras exchanges
- [ ] Implementação de novas estratégias de trading

## 🤝 Contribuidores

<table>
    <tr>
        <td align="center">
            <a href="https://www.instagram.com/jaonativi/" title="Desenvolvedor Principal">
                <img src="https://avatars.githubusercontent.com/u/87316339?v=4" width="100px;" alt="Foto de João da Cruz no GitHub"/><br>
                <sub>
                    <b>João da Cruz</b>
                </sub>
            </a>
        </td>
    </tr>
</table>

## Como Executar

1. Clone o repositório:
   ```sh
   git clone https://github.com/seu-usuario/crypto-trading-bot.git
   cd crypto-trading-bot
   ```
2. Instale o `uv` no seu computador https://github.com/astral-sh/uv
3. Instale as dependências:
   ```sh
   uv sync --dev
   ```
4. Configure as credenciais da API da Bitypreço no arquivo `.env`.
5. Instale o talib em sua máquina para mais informações acesse https://ta-lib.org/install/
6. Execute o bot:
   ```sh
   task bot
   ```
7. Acesse o dashboard em `http://localhost:8050` para visualizar dados de mercado e desempenho do bot.
    ```sh
    task run
    ```

## 📫 Contribuindo para o Projeto

Se você deseja contribuir para o desenvolvimento do projeto, siga os passos abaixo:

1. Faça um fork do repositório
2. Clone o fork para o seu ambiente local
3. Crie uma branch para suas alterações (`git checkout -b nome-da-sua-branch`)
4. Faça commit das suas alterações (`git commit -m 'Descrição das alterações'`)
5. Faça push para a branch (`git push origin nome-da-sua-branch`)
6. Abra um pull request no repositório original

## Licença

Este projeto está licenciado sob a Licença MIT. Veja o arquivo LICENSE para mais detalhes.