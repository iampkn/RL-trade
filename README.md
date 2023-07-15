# Reinforcement Learning for Stock Trading

This repository contains a Python script that implements a reinforcement learning approach for stock trading using Deep Q-Networks (DQN). The code trains an agent to make trading decisions based on historical stock price data.

## Features

- Uses a multi-layer perceptron (MLP) or LSTM model architecture for the DQN agent.
- Implements experience replay memory for efficient training.
- Supports training and testing modes.
- Provides a customizable trading environment for multiple stocks.
- Saves and loads trained models and scaling parameters.
- Calculates and saves portfolio values for each episode.

## Requirements

- Python 3.7+
- TensorFlow 2.0+
- NumPy
- Pandas
- Scikit-learn

## Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/your-username/reinforcement-trading.git
   cd reinforcement-trading
   ```

2. Create a virtual environment (optional but recommended):

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. Install the dependencies:

   ```bash
   pip install -r requirements.txt
   ```

## Usage

The code can be run in either training or testing mode. Follow the instructions below to use the code:

### Training Mode

To train the DQN agent on stock price data, run the following command:

```bash
python main.py -m train
```

This will initiate the training process with the default configuration. The script will save the trained model, as well as the scaling parameters, in the `rl_trader_models` directory.

### Testing Mode

To test the trained agent on new stock price data, follow these steps:

1. Ensure that the trained model (`dqn.h5`) and the scaling parameters (`scaler.pkl`) are present in the `rl_trader_models` directory.

2. Place the new stock price data in a CSV file with the same format as the provided `aapl_msi_sbux.csv` file.

3. Run the following command:

   ```bash
   python main.py -m test
   ```

   This will load the trained model and scaling parameters and evaluate the agent's performance on the new data. The script will save the portfolio values for each episode in the `rl_trader_rewards` directory.

## Customization

The code can be customized according to your specific requirements. Here are some possible modifications:

- Adjust the configuration settings in the `__main__` block of the `main.py` file to change the number of episodes, batch size, or initial investment.

- Modify the model architecture by editing the `mlp` function to use different layer configurations or by implementing a different model type (e.g., LSTM).

- Customize the trading environment by changing the stocks, adding new features to the state representation, or modifying the action space.
