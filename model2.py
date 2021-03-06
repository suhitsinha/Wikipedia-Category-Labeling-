
# coding: utf-8

# In[1]:

import tensorflow as tf


# In[ ]:

class Model2:
    def __init__(self,maxParagraphLength,maxParagraphs,labels,vocabularySize):
        '''
        Constructor
        '''
        self.wordEmbeddingDimension = 50
        self.vocabularySize = vocabularySize
        self.labels = labels
        self.filterSizes_paragraph = [3]
        self.paragraphLength = maxParagraphLength
        self.num_filters_paragraph = 50
        self.maxParagraph = maxParagraphs
        self.poolLength = 50
        self.fullyConnectedLayerInput = int(maxParagraphLength*self.num_filters_paragraph/self.poolLength)
        
        self.wordEmbedding = tf.Variable(tf.random_uniform([self.vocabularySize, self.wordEmbeddingDimension], -1.0, 1.0),name="wordEmbedding")

        self.paragraphList = []
        for i in range(self.maxParagraph):
            self.paragraphList.append(tf.placeholder(tf.int32,[self.paragraphLength],name="paragraphPlaceholder"+str(i)))

        self.target = tf.placeholder(tf.float32,[self.labels],name="target")
        
        
        self.graph()
        self.session = tf.Session()
        self.session.run(tf.global_variables_initializer())
        
    
    def graph(self):
        device_name='gpu'
        with tf.device(device_name): 
            self.prediction, self.paragraph_prediction = self.convLayerCombineParagraph(self.paragraphList,self.filterSizes_paragraph,self.num_filters_paragraph)
            self.cross_entropy = -tf.reduce_sum(((self.target*tf.log(self.prediction + 1e-9)) + ((1-self.target) * tf.log(1 - self.prediction + 1e-9)) )  , name='xentropy' ) 
            self.cost = tf.reduce_mean(self.cross_entropy)
            self.optimizer = tf.train.AdamOptimizer(learning_rate=1e-4).minimize(self.cost)
    
    
    def getParagraphEmbedding(self,paragraphWords):
        device_name='gpu'
        with tf.device(device_name): 
            paraEmbedding=tf.nn.embedding_lookup(self.wordEmbedding,paragraphWords)
    
        return tf.expand_dims(tf.expand_dims(paraEmbedding, -1),0)
    
    
    
    def convLayeronParagraph(self,paragraphVector,filterSizes,num_input_channels,num_filters):
    
        pooled_outputs=[]
        for filter_size in filterSizes:
            shape = [filter_size,self.wordEmbeddingDimension,1,num_filters]

            weights = tf.Variable(tf.truncated_normal(shape, stddev=0.1),name="paragraphConvLayerW_"+str(filter_size))
            bias= tf.Variable(tf.constant(0.1, shape=[num_filters]),name="paragraphConvLayerB_"+str(filter_size))
            conv = tf.nn.conv2d(
                        paragraphVector,
                        weights,
                        strides=[1, 1, self.wordEmbeddingDimension, 1],
                        padding="SAME",
                        name="conv")

            h = tf.nn.relu(tf.nn.bias_add(conv, bias), name="relu")
            pool_length=self.poolLength
            pooled = tf.nn.max_pool(
                        h,
                        ksize=[1, pool_length, 1, 1],
                        strides=[1, pool_length, 1, 1],
                        padding='SAME',
                        name="pool")
            pooled_outputs.append(pooled)
        return tf.reshape(tf.concat(pooled_outputs,axis=0),[1,-1])

    
    
    def convLayerCombineParagraph(self,paragraphVectorList,filterSizes_paragraph,num_filters_parargaph):
    
        paragraphLogit=[]
        shape = [self.fullyConnectedLayerInput,self.labels]
        weights =tf.Variable(tf.truncated_normal(shape, stddev=0.1),name="FC_W")
        bias = tf.Variable(tf.constant(0.1, shape=[self.labels]),name="FC_Bias")
        for paragraph in paragraphVectorList:
            paragraphVector = self.getParagraphEmbedding(paragraph)
            cnnEmbedding = self.convLayeronParagraph(paragraphVector,filterSizes_paragraph,1,num_filters_parargaph)
            expandedCNNEmbedding = tf.reshape(cnnEmbedding,[1,-1])
        
            logit=tf.matmul(expandedCNNEmbedding,weights)+bias
            logit = tf.nn.sigmoid(logit)
        
            paragraphLogit.append(tf.squeeze(logit))
    
        paragraphLogitStacked = tf.stack(paragraphLogit)
        maxLogit = tf.reduce_max(paragraphLogitStacked,axis=0)  
        return maxLogit, paragraphLogitStacked
    '''
    def fullyConnectedLayer(self,convOutput,labels):
        shape = [self.fullyConnectedLayerInput,labels]
        weights =tf.Variable(tf.truncated_normal(shape, stddev=0.1),name="FC_W")
        bias = tf.Variable(tf.constant(0.1, shape=[labels]),name="FC_Bias")
        layer = tf.nn.sigmoid(tf.matmul(convOutput, weights) + bias)
        return layer
    '''
    def train(self,data):
        feed_dict_input={}
        feed_dict_input[self.target]=data[0]
        for p in range(self.maxParagraph):
            feed_dict_input[self.paragraphList[p]]= data[1][p]
        _, cost = self.session.run((self.optimizer,self.cost),feed_dict=feed_dict_input)
        return cost

    def predict(self,data):
        feed_dict_input={}
#         feed_dict_input[self.target]=data[0]
        for p in range(self.maxParagraph):
            feed_dict_input[self.paragraphList[p]]= data[1][p]
        pred=self.session.run((self.prediction,self.paragraph_prediction) ,feed_dict=feed_dict_input)
        return pred
          

    def save(self,save_path):
        saver = tf.train.Saver()
        saver.save(self.session, save_path)


    def load(self,save_path):
        self.session = tf.Session()
#         new_saver = tf.train.import_meta_graph(save_path)
        new_saver = tf.train.Saver()
        new_saver.restore(self.session, save_path)


    def save_label_embeddings(self):
        pass

