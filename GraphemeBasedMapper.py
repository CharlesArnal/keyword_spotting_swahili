import xml.etree.ElementTree as ET
import numpy as np
from collections import OrderedDict
from Index import Speech_entity

class Grapheme_Based_Mapper():
        """
        Stores vocabulary from a .dct file and confusion matrix from a .map file,
        and replaces OOV words in queries with closest IV words. More precisely:

        - self.confusion_matrix is a dictionary of dictionaries. Example:
        - self.confusion_matrix["a"]["t"] = log(P("t" recognized| "a" reference))
        - self.vocabulary is a set (for O(1) access on average)
        - self.map_to_proxy_IV_words is a dictionary that stores (in order not to do the same computations twice)
        the closest IV word associated to an OOV word (once it has appeared in a query)

        - load_confusion_matrix reads a .map file and stores the information in self.confusion_matrix
        - read_dct_get_vocabulary reads a .dct file (which maps IV words to their morphological decomposition)
        and stores the vocabulary in self.vocabulary (the morphological decomposition is ignored)
        - map_XML_queries_into_proxy_IV_XML_queries reads a XML file of queries and replaces every OOV word
        by the closes IV word using self.closest_IV_word
        - closest_IV_word(word) finds the closest word in self.vocabulary for the distance given by self.distance
        - distance(word1,word2) computes the log likelihood of word2 being recognized when word1 was said
        (it is not really a distance; in particular, it is not symmetric)
        The distance is computed using the confusion matrix and a variant of the Wagner-Fisher algorithm

        """
        def __init__(self):
                self.confusion_matrix=dict()
                self.vocabulary={}
                self.map_to_proxy_IV_words=dict()

        def load_confusion_matrix(self,path_to_grapheme_confusion_file):
                self.confusion_matrix=dict()
                grapheme_map = open(path_to_grapheme_confusion_file,"r")
                for line in grapheme_map:
                        ref_grapheme = line.split()[0]
                        obs_grapheme = line.split()[1]
                        count = float(line.split()[2])
                        if ref_grapheme not in self.confusion_matrix:
                                self.confusion_matrix[ref_grapheme] = dict()
                                self.confusion_matrix[ref_grapheme]["total_count"] = 0
                        self.confusion_matrix[ref_grapheme][obs_grapheme] = count
                        self.confusion_matrix[ref_grapheme]["total_count"] += count
                for grapheme in self.confusion_matrix:
                        for observation in self.confusion_matrix[grapheme]:
                                if observation != "total_count":
                                        self.confusion_matrix[grapheme][observation] = np.log((self.confusion_matrix[grapheme][observation])/(self.confusion_matrix[grapheme]["total_count"])) 

        # rmk: non-symetric, word1 is the reference word and word2 is the observed word
        def distance(self,word1,word2):
                m1 = len(word1)
                m2 = len(word2)
                D = dict()
                for i in range(m1+1):
                        for j in range(m2+1):
                                D[i,j] = 0
                for i in range(1,m1+1,1):
                                D[i,0] = D[i-1,0] + self.deletion_penalty(word1[i-1])
                for j in range(1,m2+1,1):
                        D[0,j] = D[0,j-1] + self.insertion_penalty(word2[j-1])
                for i in range(1,m1+1,1):
                        for j in range(1,m2+1,1):
                                D[i,j] =   max(D[i-1,j] +  self.deletion_penalty(word1[i-1]), D[i,j-1] + self.insertion_penalty(word2[j-1]), D[i-1,j-1] + self.substitution_penalty(word1[i-1],word2[j-1]))
                return -D[m1,m2]

        def deletion_penalty(self,character):
                if "sil" in self.confusion_matrix[character]:
                        return self.confusion_matrix[character]["sil"]
                else:
                        return -40
        def insertion_penalty(self,character):
                if character in self.confusion_matrix["sil"]:
                        return self.confusion_matrix["sil"][character]
                else:
                        return -40
        def substitution_penalty(self,character1,character2):
                if character2 in self.confusion_matrix[character1]:
                        return self.confusion_matrix[character1][character2]
                else:
                        return -40

        def read_dct_get_vocabulary(self,path_to_dictionary_document):
                vocabulary=[]
                f = open(path_to_dictionary_document,"r")
                for line in f:
                        vocabulary.append(line.split()[0])
                # to make access O(1) on average
                self.vocabulary = set(vocabulary)

        def map_XML_queries_into_proxy_IV_XML_queries(self,path_to_XML_input,path_to_XML_output):
                tree=ET.parse(path_to_XML_input)
                root = tree.getroot()
                for kw in root:
                        query_words = kw[0].text.split()
                        new_query_words = []
                        for word in query_words:
                                if word not in self.vocabulary:
                                        word = word.lower()
                                        word = "".join(letter for letter in word if letter.isalnum())
                                        if word not in self.map_to_proxy_IV_words:
                                                self.map_to_proxy_IV_words[word] = self.closest_IV_word(word)
                                        new_query_words.append(self.map_to_proxy_IV_words[word])
                                else:
                                        new_query_words.append(word)
                        kw[0].text = " ".join(new_query_words)
                tree.write(path_to_XML_output)

        def closest_IV_word(self,word):
                distances=dict()
                for IV_word in self.vocabulary:
                        distances[IV_word]=self.distance(word.replace("'",""),IV_word.replace("'",""))
                return min(distances, key=distances.get)