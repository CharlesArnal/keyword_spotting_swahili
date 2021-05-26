import xml.etree.ElementTree as ET
import numpy as np
from collections import OrderedDict
from Index import Speech_entity


class Morph_Decomposer():
        """
        Stores morphological decomposition mappings from .dct files and performs decomposition on CTM ASR output files and XML query lists files
        
        Mappings are stored using load_decomposition_mapping_decoded_speech and load_decomposition_mapping_query_list
        in self.decomposition_mapping_decoded_speech and self.decomposition_mapping_query_list as dictionaries
        (where for example self.decomposition_mapping_decoded_speech["weekend"] = ["week","end"])

        morph_decompose_CTM_decoding and morph_decompose_XML_queries then read a CTM or XML file and output a file of the same format
        where morphological decomposition has been applied

        When a word entry in a CTM file which had a duration of T and a posterior probability of p gets decomposed into n subwords,
        each is attributed a duration of T/n and a posterior probability of p^(1/n), so that the sequence of subwords has
        the same duration and posterior probability as the original word
        """
        def __init__(self):
                self.decomposition_mapping_decoded_speech=dict()
                self.decomposition_mapping_query_list=dict()
                self.vocabulary=[]
        
        def load_decomposition_mapping_decoded_speech(self,path_to_dictionary_document):
                self.decomposition_mapping_decoded_speech = self.read_dct_output_dictionary(path_to_dictionary_document)
                
        def load_decomposition_mapping_query_list(self,path_to_dictionary_document):
                self.decomposition_mapping_query_list = self.read_dct_output_dictionary(path_to_dictionary_document)

        def read_dct_output_dictionary(self,path_to_dictionary_document):
                decomposition_dictionary = dict()
                f = open(path_to_dictionary_document,"r")
                for line in f:
                        decomposition_dictionary[line.split()[0]]=line.split()[1:]
                return decomposition_dictionary
        
        def morph_decompose_CTM_decoding(self,path_to_CTM_input,path_to_CTM_output):
                f_input = open(path_to_CTM_input,"r")
                f_output =open(path_to_CTM_output,"w")
                for line in f_input:
                        entry = Speech_entity(line)
                        [file_name, channel, tbeg, tdur, tend,word, posterior] = entry.get_values()
                        if word in self.decomposition_mapping_decoded_speech:
                                decomposed_word = self.decomposition_mapping_decoded_speech[word]
                                n = len(decomposed_word)
                                decomposed_posterior = str(np.round(np.power(posterior,1/n),6))
                                decomposed_duration = np.round(tdur/n,2)
                                for index, subword in enumerate(decomposed_word):
                                        new_line = " ".join([file_name, channel, str(tbeg + index*decomposed_duration),str(decomposed_duration),subword,decomposed_posterior]) + "\n"
                                        f_output.write(new_line)
                        else:
                                f_output.write(line)

        def morph_decompose_XML_queries(self,path_to_XML_input,path_to_XML_output):
                tree=ET.parse(path_to_XML_input)
                root = tree.getroot()
                for kw in root:
                        kw[0].text = " ".join([" ".join(self.decomposition_mapping_query_list[word]) if word.lower() in self.decomposition_mapping_query_list  else word.lower() for word in kw[0].text.split()])
                tree.write(path_to_XML_output)
                
               