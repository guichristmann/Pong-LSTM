# Pong LSTM with Keras
A LSTM experiment, training a model to predict the next frame in a Pong game.
This is based on a simple [PyGame Pong clone](https://github.com/guichristmann/Pong) I've made and Keras with
Tensorflow backend.

## Data Generation
The data used for training is generated logging some information from the game each frame,
and dumping them into text files, which I've called sessions. The pieces of data used and their logged format is as follows:

**ball_x:ball_y:vel_x:vel_y:p1_x:p1_y:p2_x:p2_y:hit_p1:hit_p2:p1_up:p1_down:p2_up:p2_down**

* ball_x and ball_y: x and y coordinates of the ball on the screen respectively. Ranges between 0 and 1, normalized to the sizes of the screen. (e.g. absolute coordinate [300, 400] becomes [0.47, 0.83] on 640x480 resolution)
* vel_x and vel_y: unity vector of the velocity of the ball on x and y directions. Ranges between -1 and 1.
* p1_x and p1_y: x and y coordinates of Paddle 1 on the screen. Ranges between 0 and 1, normalized to the sizes of the screen.
* p2_x and p2_y: x and y coordinates of Paddle 2 on the screen. Ranges between 0 and 1, normalized to the sizes of the screen.
* hit_p1 and hit_p2: Becomes 1 in the frame a Paddle (1 or 2) is hit, else is 0.
* p1_up and p1_down: Button presses for Player 1. A binary, 0 or 1.
* p2_up and p2_down: Button presses for Player 2. A binary, 0 or 1.

Each line of a log session is a frame of the game with all the information presented above.

#### *pong_cpu_sessions.py*
For now, I've implemented a version of the Game with a simple CPU-controlled AI for generating enough data to build and debug LSTM models.
Usage: *python pong_cpu_sessions.py <logs-folder>*
Receives a path to a folder as an argument, where the log sessions will be dumped. A new session is created each time a point is scored for either side.

## Training
Training is performed by randomly selecting a number of log sessions for each epoch. Each session is imported as a numpy array and reformatted for LSTM training - (samples, timesteps, features). A parameter called HISTORY_SIZE defines the number of timesteps (or frames) from which the LSTM will learn to predict the next. An X, Y pair for training will contain frame **I** to **HISTORY_SIZE** for X and frame **I+HISTORY_SIZE+1** For Y, and so on for each frame of the log session. An important thing to note is that data is not shuffled (parameter shuffle=False when fitting the model with Keras), so X, Y pairs are presented to the LSTM in sequence.

#### *train_model.py*
Usage: *python train_model.py <log-sessions-path> <model-name>*
First argument is the path to folder containing the sessions. Second argument is the name of model to save.

## "Playing" with a Model

#### *pong_lstm.py*
Usage: *python pong_lstm.py <model>*
Receives a path to a model as argument.

The engine runs for the first *HISTORY_SIZE* frames to give some initial frames for the LSTM to perform its first prediction and from then on the **Lstm_Input()** function will take care of the rest of the game. This is effectively how the model "imagines" a pong game.


## Some Results

#### *200lstm_final.h5*

A single 200 LSTM layer, followed by a Dense 14 output layer. Output activation is 'tanh'.
Trained with a batch size of 3000 and HISTORY_SIZE=30, making its predictions based on the last 30 frames. Trained for 10000 epochs.

![200 LSTM](/git_data/200lstm.gif)

#### *deeplstm_8451.h5*

"Deep" is kind of an overstatement. 200-LSTM -> 100-LSTM -> 50-LSTM -> 14-Dense with 'tanh' activation.
Batch size of 1500 (larger batches weren't fitting into memory :( ) and HISTORY_SIZE of 30. Trained for 8451 epochs.

!["Deep" LSTM](/git_data/deeplstm.gif)
