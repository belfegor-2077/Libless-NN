import math
import random
E = math.e
random.seed(0)
import csv
import numpy as np


class Layer:
    def __init__(self, previous_height, height, activation_function_type):
        self.biases = np.array([1 * (random.random() * 2 - 1) for n in range(height)])
        self.weights = np.array([[(1 * (random.random()) * 2 - 1) for n in range(previous_height)] for m in range(height)])
        self.delta_biases = np.array([0] * height)
        self.delta_weights = np.array([[0] * previous_height for n in range(height)])
        self.activation_function_type = activation_function_type
        self.t = 0
        self.m = None
        self.v = None
        self.m_weights = np.zeros_like(self.weights)
        self.v_weights = np.zeros_like(self.weights)
        self.m_biases = np.zeros_like(self.biases)
        self.v_biases = np.zeros_like(self.biases)

    def forward(self, previous_layer_outputs):
        self.previous_layer_outputs = previous_layer_outputs
        self.outputs = np.dot(previous_layer_outputs,self.weights.T) + self.biases
        
    def initialize_optimizer(self, beta1, beta2, epsilon, learning_rate):
        self.learning_rate = learning_rate
        self.beta1 = beta1
        self.beta2 = beta2
        self.epsilon = epsilon

    def activation_function(self):
        if self.activation_function_type == "None":
            self.post_activation_outputs = self.outputs
        elif self.activation_function_type == "ReLU":
            self.post_activation_outputs = [max(0, n) for n in self.outputs]
        elif self.activation_function_type == "Leaky_ReLU":
            self.post_activation_outputs = [0.01 * n if n < 0 else n for n in self.outputs]
        elif self.activation_function_type == "Softmax":
            exp_outputs = np.exp(self.outputs - np.max(self.outputs))
            self.post_activation_outputs = exp_outputs / np.sum(exp_outputs)
        elif self.activation_function_type == "Sigmoid":
            self.post_activation_outputs = [1/(1 + E**(-n)) for n in self.outputs]
        elif self.activation_function_type == "Sigmoid":
            self.post_activation_outputs = [1 / (1 + np.exp(-n)) for n in self.outputs]
            self.post_activation_outputs = np.clip(self.post_activation_outputs, 1e-15, 1 - 1e-15)

    def loss(self, prediced_list, expected_list, type):
        self.loss_type = type
        if self.loss_type == "mse":
            self.mean_loss = 0.5*(sum((prediced_list[i]-expected_list[i])**2 for i in range(len(prediced_list))))/len(prediced_list)
            self.d_loss = [(prediced_list[i] - expected_list[i]) for i in range(len(prediced_list))]
        elif self.loss_type == "log":
            self.mean_loss = sum(-expected_list[i] * math.log(self.post_activation_outputs[i] + 1e-15) for i in range(len(self.post_activation_outputs)))
            self.d_loss = [self.post_activation_outputs[i]-expected_list[i] for i in range(len(self.post_activation_outputs))]

    def back_prop(self, inputted_loss_array):
        self.passed_on_loss_array = [0 if self.outputs[i] < 0 and self.activation_function_type == "ReLU" else 0.01 * inputted_loss_array[i] if self.outputs[i] < 0 and self.activation_function_type == "Leaky_ReLU" else inputted_loss_array[i] for i in range(len(inputted_loss_array))]
        self.delta_biases = self.delta_biases + np.array(self.passed_on_loss_array)
        self.delta_weights = self.delta_weights.astype('float64')
        self.delta_weights += np.outer(self.passed_on_loss_array, self.previous_layer_outputs)
        self.loss_to_pass = np.dot(self.passed_on_loss_array, self.weights)

    def update_w_and_b(self, batch_size):
        self.t += 1

        self.delta_weights = (1 / batch_size) * np.array(self.delta_weights)
        self.m_weights = self.beta1 * self.m_weights + (1 - self.beta1) * self.delta_weights
        self.v_weights = self.beta2 * self.v_weights + (1 - self.beta2) * (self.delta_weights * self.delta_weights)
        m_hat = (1 / (1 - self.beta1 ** self.t)) * self.m_weights
        v_hat = (1 / (1 - self.beta2 ** self.t)) * self.v_weights
        self.weights = self.weights - self.learning_rate * (1 / (np.sqrt(v_hat) + self.epsilon)) * m_hat

        self.delta_biases = (1 / batch_size) * np.array(self.delta_biases)
        self.m_biases = self.beta1 * self.m_biases + (1 - self.beta1) * self.delta_biases
        self.v_biases = self.beta2 * self.v_biases + (1 - self.beta2) * (self.delta_biases * self.delta_biases)
        m_hat = (1 / (1 - self.beta1 ** self.t)) * self.m_biases
        v_hat = (1 / (1 - self.beta2 ** self.t)) * self.v_biases
        self.biases = self.biases - self.learning_rate * (1 / (np.sqrt(v_hat) + self.epsilon)) * m_hat

        self.delta_biases = np.zeros_like(self.biases)
        self.delta_weights = np.zeros_like(self.weights)


class NN:
    def __init__(self, input_size, inner_layers_number, height, output_size, inner_layer_activation, last_layer_activation):
        self.inner_layer_activation = inner_layer_activation
        self.last_layer_activation = last_layer_activation
        self.layers = [[]] * (inner_layers_number + 2)
        self.layers[0] = Layer(input_size, height, inner_layer_activation)
        self.layers[-1] = Layer(height, output_size, last_layer_activation)
        for i in range(inner_layers_number):
            self.layers[i+1] = Layer(height, height, inner_layer_activation)
    
    def initialize_optimizer(self, beta1, beta2, epsilon, learning_rate):
        for i in range(len(self.layers)):
            self.layers[i].initialize_optimizer(beta1, beta2, epsilon, learning_rate)

    def train(self, epochs, training_data, training_answers, batch_size):
        current_epoch = 0
        current_batch = 0
        for i in range(epochs):
            current_epoch_loss = 0
            batch_loss = 0
            combined_data = list(zip(training_data, training_answers))
            # Shuffle the combined data
            random.shuffle(combined_data)
            # Split the shuffled data back into training_data and training_answers
            training_data, training_answers = zip(*combined_data)
            for j in range(len(training_data)):
                current_batch += 1
                #start layer forward and activation
                self.layers[0].forward(training_data[j])
                self.layers[0].activation_function()
                #middle layer forward and activation
                for k in range(len(self.layers)-2):
                    self.layers[k+1].forward(self.layers[k].post_activation_outputs)
                    self.layers[k+1].activation_function()
                #last layer forward and activation
                self.layers[-1].forward(self.layers[-2].post_activation_outputs)
                self.layers[-1].activation_function()
                #now for loss
                loss_function = "log" if self.last_layer_activation == "Softmax" else "mse"
                self.layers[-1].loss(self.layers[-1].post_activation_outputs, training_answers[j],loss_function)
                batch_loss += self.layers[-1].mean_loss
                current_epoch_loss += self.layers[-1].mean_loss
                #now for back prop
                self.layers[-1].back_prop(self.layers[-1].d_loss)
                for l in range(len(self.layers)-1):
                    self.layers[-l-2].back_prop(self.layers[-l-1].loss_to_pass)
                if current_batch == batch_size:
                    current_batch = 0
                    # print(f"{round(batch_loss/batch_size,3)}")
                    for g in range(len(self.layers)):
                        self.layers[g].update_w_and_b(batch_size)
                    batch_loss = 0
            if current_batch != 0:
                for k in range(len(self.layers)):
                    self.layers[k].update_w_and_b(batch_size)
            current_epoch += 1
            print(f"Epochs completed: {current_epoch}/{epochs} |Average epoch loss: {current_epoch_loss/len(training_data)}")

    def predict(self, data_to_predict):
        self.prediction_outputs = []
        print(f"Predicting")
        for i in range(len(data_to_predict)):
            self.layers[0].forward(data_to_predict[i])
            self.layers[0].activation_function()
            #middle layer forward and activation
            for k in range(len(self.layers)-2): 
                self.layers[k+1].forward(self.layers[k].post_activation_outputs)
                self.layers[k+1].activation_function()
            #last layer forward and activation
            self.layers[-1].forward(self.layers[-2].post_activation_outputs)
            self.layers[-1].activation_function()
            self.prediction_outputs.append(self.layers[-1].post_activation_outputs)

    def export_weights(self):
        all_weights = []
        for i in range(len(self.layers)):
            all_weights.append(self.layers[i].weights)
        return(all_weights)
    
    def export_biases(self):
        all_biases = []
        for i in range(len(self.layers)):
            all_biases.append(self.layers[i].biases)
        return(all_biases)

def one_hot_encoding(data, data_types):
    output = []
    for i in range(len(data)):
        output.append([])
        for j in range(data_types):
            if j == data[i]:
                output[i].append(1)
            else:
                output[i].append(0)
    return(output)

questions = []
labels = []
with open("Iris.csv", "r") as file:
    csv_reader = csv.reader(file)
    next(csv_reader)
    for row in csv_reader:
        feature_row = list(map(float, row[1:5]))
        label = row[5]
        questions.append(feature_row)
        labels.append(label)
for i in range(len(questions)):
    if labels[i] == "Iris-setosa":
        labels[i] = 0
    elif labels[i] == "Iris-versicolor":
        labels[i] = 1
    elif labels[i] == "Iris-virginica":
        labels[i] = 2


class QuestionsAndAnswers():
    def __init__(self, questions, answers, amount):
        combined_data = list(zip(questions, answers))
        # Shuffle the combined data
        random.shuffle(combined_data)
        # Split the shuffled data back into training_data and training_answers
        questions, answers = zip(*combined_data)

        self.training_data_questions = questions[:amount]
        self.training_data_answers = answers[:amount]
        self.prediction_data_questions = questions[amount:]
        self.prediction_data_answers = answers[amount:]

    def get_t_q(self):
        return self.training_data_questions
    def get_t_a(self):
        return self.training_data_answers
    def get_p_q(self):
        return self.prediction_data_questions
    def get_p_a(self):
        return self.prediction_data_answers

iris_data = QuestionsAndAnswers(questions, one_hot_encoding(labels,3), 99)

def prediction_check(prediction, actual, is_classification):
        # print(f"\nPredictions:\n{prediction}")
        if actual is not None and len(actual) > 0:
            if is_classification == True:
                total_correct = sum(1 for pred, actual_row in zip(prediction, actual) if np.argmax(pred) == np.argmax(actual_row))
                print(f"\nTotal accuracy: {round((total_correct/len(prediction))*100,5)} %")
            else:
                losses = [sum(0.5 * (prediction[i][j] - actual[i][j]) ** 2 for j in range(len(prediction[0]))) / len(prediction[0]) for i in range(len(prediction))]
                total_avg_loss = sum(losses)/len(losses)
                print(f"\nMean loss: {round(total_avg_loss,5)}")
                print(f"\nAll losses: \n{losses}")

def train_and_test(input_size, 
                   inner_layers_amount, 
                   neurons_per_layer, 
                   output_size, 
                   inner_neuron_activation, 
                   last_layer_activation, 
                   epochs, learning_rate, 
                   training_questions, 
                   training_answers, 
                   batch_size, 
                   predict_questions, 
                   predict_answers, 
                   is_classification,
                   beta1,
                   beta2,
                   epsilon):
    neural = NN(input_size, inner_layers_amount, neurons_per_layer, output_size, inner_neuron_activation, last_layer_activation)
    neural.initialize_optimizer(beta1, beta2, epsilon, learning_rate)
    neural.train(epochs, training_questions, training_answers, batch_size)
    neural.predict(predict_questions)
    prediction_check(neural.prediction_outputs, predict_answers, is_classification)
    # print(f"\nWeights:\n{neural.export_weights()}\n\nBiases:\n{neural.export_biases()}")

train_and_test(input_size = 4, 
               inner_layers_amount = 3, 
               neurons_per_layer = 16, 
               output_size = 3, 
               inner_neuron_activation = "Leaky_ReLU", 
               last_layer_activation = "Sigmoid", 
               epochs = 10,
               learning_rate = 0.01,
               training_questions = iris_data.get_t_q(),
               training_answers = iris_data.get_t_a(),
               batch_size = 16,
               predict_questions = iris_data.get_p_q(),
               predict_answers = iris_data.get_p_a(),
               is_classification = True,
               beta1 = 0.9,
               beta2 = 0.999,
               epsilon = 1e-8)