# Alternative Project: Algorithmic Trading System with Reinforcement Learning for Cryptocurrency Markets

![GitHub repo size](https://img.shields.io/github/repo-size/joaosnet/crypto?style=for-the-badge)
![GitHub language count](https://img.shields.io/github/languages/count/joaosnet/crypto?style=for-the-badge)
![GitHub forks](https://img.shields.io/github/forks/joaosnet/crypto?style=for-the-badge)
![Bitbucket open issues](https://img.shields.io/bitbucket/issues/joaosnet/crypto?style=for-the-badge)
![Bitbucket open pull requests](https://img.shields.io/bitbucket/pr-raw/joaosnet/crypto?style=for-the-badge)
[![Language: pt-br](https://img.shields.io/badge/lang-pt--br-green.svg?style=for-the-badge)](https://github.com/joaosnet/crypto/blob/master/README.pt-br.md)

## Project Description

The cryptocurrency market is known for its high volatility and continuous operation, which presents unique opportunities for automated trading strategies. This project aims to develop an algorithmic trading system that uses Reinforcement Learning (RL) techniques to optimize buy and sell decisions for cryptocurrencies, specifically Bitcoin, in real-time.

## Skills Developed
<img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white" /> <img src="https://img.shields.io/badge/Pandas-150458?style=for-the-badge&logo=pandas&logoColor=white" /> <img src="https://img.shields.io/badge/TA--Lib-3776AB?style=for-the-badge&logo=python&logoColor=white" /> <img src="https://img.shields.io/badge/OpenAI_Gym-232F3E?style=for-the-badge&logo=openai&logoColor=white" /> <img src="https://img.shields.io/badge/Stable_Baselines3-232F3E?style=for-the-badge&logo=openai&logoColor=white" /> <img src="https://img.shields.io/badge/Dash-232F3E?style=for-the-badge&logo=dash&logoColor=white" />

# Table of Contents

* [Project Description](#project-description)
* [Skills Developed](#skills-developed)
* [Objectives](#objectives)
    * [General](#general)
    * [Specific](#specific)
    * [Adjustments and Improvements](#adjustments-and-improvements)
* [🤝 Contributors](#-contributors)
* [How to Run](#how-to-run)
* [📫 Contributing to the Project](#-contributing-to-the-project)

## Objectives

### General

Develop a modular algorithmic trading bot that:
1. Continuously captures market data from the Bitypreço API (exchange).
2. Uses technical indicators to make buy and sell decisions.
3. Implements Reinforcement Learning strategies to optimize these decisions.

### Specific

- **Data Collection**: The bot continuously captures market data, such as prices, volumes, and other technical indicators, from the Bitypreço API.
- **Technical Analysis**: Uses technical indicators like RSI, MACD, Bollinger Bands, Stochastic, among others, to identify buy and sell signals.
- **Order Execution**: Based on the generated signals, the bot executes buy and sell orders for cryptocurrencies.
- **Reinforcement Learning**: Implements RL agents that learn and optimize trading strategies based on historical and real-time data.
- **Backtesting**: Allows testing different trading strategies on historical data to evaluate their effectiveness before applying them in real-time.

### Adjustments and Improvements

The project is under continuous development, and the next updates will focus on the following tasks:

- [x] Data Collection
- [x] Technical Analysis
- [x] Order Execution
- [x] Backtesting
- [ ] Reinforcement Learning
- [ ] Integration with other exchanges
- [ ] Implementation of new trading strategies

## 🤝 Contributors

<table>
    <tr>
        <td align="center">
            <a href="https://www.instagram.com/jaonativi/" title="Main Developer">
                <img src="https://avatars.githubusercontent.com/u/87316339?v=4" width="100px;" alt="Photo of João da Cruz on GitHub"/><br>
                <sub>
                    <b>João da Cruz</b>
                </sub>
            </a>
        </td>
    </tr>
</table>

## How to Run

1. Clone the repository:
   ```sh
   git clone https://github.com/joaosnet/crypto.git
   cd crypto
   ```
2. Install `uv` on your computer https://github.com/astral-sh/uv
3. Install the dependencies:
   ```sh
   uv sync --dev
   ```
4. Configure the Bitypreço API credentials in the `.env` file.
5. Install talib on your machine for more information visit https://ta-lib.org/install/
6. Run the bot:
   ```sh
   task bot
   ```
7. Access the dashboard at `http://localhost:8050` to view market data and bot performance.
    ```sh
    task run
    ```

## 📫 Contributing to the Project

If you want to contribute to the project development, follow the steps below:

1. Fork the repository
2. Clone the fork to your local environment
3. Create a branch for your changes (`git checkout -b your-branch-name`)
4. Commit your changes (`git commit -m 'Description of changes'`)
5. Push to the branch (`git push origin your-branch-name`)
6. Open a pull request in the original repository

## License

This project is licensed under the MIT License. See the LICENSE file for more details.
