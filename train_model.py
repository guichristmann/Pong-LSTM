import numpy as np
from keras.models import Sequential 
from keras.optimizers import *
from keras.layers import *
import random
import sys
import pickle
from glob import glob

HISTORY_SIZE = 30 # how many frames consist a sample
BATCH_SIZE = 3000
SESSIONS_PER_EPOCH = 15

#np.random.seed(10)

def loadData(filename):
    data = []
    with open(filename, 'r') as f:
        lines = f.readlines()
    
    for l in lines:
        data.append([float(i) for i in l.split(':')])

    return np.array(data)

def getSessions(path, n_sessions=1):
    logs = glob(path + '/*')
    sessions = []
    for i in range(n_sessions):
        log = random.choice(logs)
        sessions.append(loadData(log))

    return sessions

# sample data and format it for lstm training
def sequentialSample(data, out_dims=1):
    global start, stop
    x = []
    y = []
    for i in range(len(data) - HISTORY_SIZE):
        x.append(data[i:i+HISTORY_SIZE])

        y.append(data[i+HISTORY_SIZE:i+HISTORY_SIZE+out_dims])

    return np.array(x), np.array(y)

if len(sys.argv) != 3:
    print "Usage:", sys.argv[0], "<log-sessions-path> <model-name>" 
    sys.exit(1)

logsessions_path = sys.argv[1] 

model = Sequential()
model.add(LSTM(50, input_shape=(HISTORY_SIZE, 14)))
model.add(Dense(14, activation='tanh'))

rmsprop = RMSprop(lr=0.005, rho=0.9, epsilon=1e-08, decay=0.001)
model.compile(loss='mse', optimizer=rmsprop, metrics=['mse'])

print model.summary()

sessions = getSessions(logsessions_path, SESSIONS_PER_EPOCH)
eval_x, eval_y = sequentialSample(sessions[0])
eval_y = eval_y.reshape(eval_y.shape[0], eval_y.shape[2])

print "[Fitting model to data]"
for i in range(1000):
    print "[Getting", SESSIONS_PER_EPOCH, "sessions from logs.]"
    sessions = getSessions(logsessions_path, SESSIONS_PER_EPOCH)
    for d in range(len(sessions)-1):
        print "### Epoch", i+1, " - Session n.", d+1, "of", SESSIONS_PER_EPOCH, "###"
        print "[Formatting data for LSTM Training]"
        x, y = sequentialSample(sessions[d])
        y = y.reshape(y.shape[0], y.shape[2])
        model.fit(x[:-120], y[:-120], epochs=1, batch_size=BATCH_SIZE, shuffle=False, verbose=2)
        model.reset_states()

    print "[Formatting data for LSTM Evaluation]"
    score = model.evaluate(eval_x, eval_y, batch_size=BATCH_SIZE)

    print "\n\nEpoch", i + 1, "results"
    print "Error:", score[0], "Accuracy:", score[1]
    model_name = sys.argv[2] + "_" + str(i+1) + ".h5"
    print "Saving model...\n"
    model.save(model_name)
