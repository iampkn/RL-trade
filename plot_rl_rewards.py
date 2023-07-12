import matplotlib.pyplot as plt
import numpy as np
import argparse

# parser = argparse.ArgumentParser()
# parser.add_argument('-m', '--mode', type=str, required=True,
#                     help='either "train" or "test"')
args = "test"
dir = "D:/machine_learning_examples/tf2.0"

a = np.load(f'{dir}/rl_trader_rewards/{args}.npy')

print(f"average reward: {a.mean():.2f}, min: {a.min():.2f}, max: {a.max():.2f}")

if args == 'train':
  # show the training progress
  plt.plot(a)
else:
  # test - show a histogram of rewards
  plt.plot(a)

plt.title(args)
plt.show()