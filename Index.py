import xml.etree.ElementTree as ET
import numpy as np
from collections import OrderedDict


class Speech_entity():
        """
        Represents an entry in a CTM ASR output file
        Then "entry" argument should be a string (en entire line of the CTM file)
        """
        def __init__(self,entry):
                split_entry=entry.split()
                self.file_name=split_entry[0]
                self.channel = split_entry[1]
                self.tbeg=float(split_entry[2])
                self.tdur=float(split_entry[3])
                self.tend=self.tbeg+self.tdur
                self.token=split_entry[4].lower()
                self.posterior=float(split_entry[5])

        def get_values(self):
                return [self.file_name,self.channel,self.tbeg,self.tdur,self.tend,self.token,self.posterior]

class Index():
        """
        Main indexing class
        Its attributes are:
        - formatted_speech : a list whose entries are either Speech_entity or None  ,
        where each entry represents either a word/subword with associated data (beginning time, etc.),
        or a silence of more than 0.5 second (in the case of None) (this makes the identification of phrases easier)
        - occurence_index: a dictionary where each word is mapped to the list of indices of the entries in formatted_speech
        where it occurs (example: occurence_index["abandon"]=[2, 36])
        Its main methods are:
        - index_CTM_document, which takes as input the path to a CTM ASR output file
        and stores its entries as Speech_entity objects in formatted_speech (it also adds None entries to represent silences of >0.5s),
        as well as creating a dictionary indexing the location of each word in the file, and storing it in occurence_index
        - perform_KWS, which takes as input the path to a XML file which is a list of queries and the path to the desired output file,
        and creates a XML file at that location which contains the list of hits
        corresponding to the queries and the current content of formatted_speech and occurence_index
        """
        def __init__(self):
                self.formatted_speech=[]
                self.occurence_index=dict()

        def get_occurence_index(self):
                return self.occurence_index
        
        def index_CTM_document(self,path_to_CTM_document):
                self.formatted_speech=[]
                self.occurence_index=dict()
                for line in open(path_to_CTM_document,"r"):
                        entry = Speech_entity(line)
                        if self.formatted_speech!=[] and (entry.tbeg - self.formatted_speech[-1].tend >0.5 ) :
                                self.formatted_speech.append(None)
                        self.formatted_speech.append(entry)
                        if self.occurence_index.get(entry.token) != None:
                                self.occurence_index[entry.token].append(len(self.formatted_speech)-1)
                        else:
                                self.occurence_index[entry.token]= [len(self.formatted_speech)-1]


        def perform_KWS(self,path_to_XML_query_list,path_to_XML_output):
                tree=ET.parse(path_to_XML_query_list)
                root = tree.getroot()
                for kw in root:
                        kw.tag = "detected_kwlist"
                        kw.attrib["oov_count"]="0"
                        kw.attrib["search_time"]= "0.0"
                        query_text=kw[0].text.split()
                        kw.remove(kw[0])
                        if self.occurence_index.get(query_text[0]) != None:
                                for partial_hit in self.occurence_index[query_text[0]]:
                                        possible_hit = self.formatted_speech[partial_hit:partial_hit+len(query_text)]
                                        tokens_in_file = [entry.token if entry!= None else None for entry in possible_hit]
                                        if tokens_in_file == query_text:
                                                hit = ET.SubElement(kw, "kw")
                                                total_proba = np.prod([entry.posterior if entry!= None else 0 for entry in possible_hit])
                                                hit.attrib = OrderedDict([("file", possible_hit[0].file_name),("channel" , possible_hit[0].channel),("tbeg" , str(possible_hit[0].tbeg)),("dur",str(np.round(possible_hit[-1].tend - possible_hit[0].tbeg,2))),("score",str(np.round(total_proba,6))),("decision","YES")])
                                                # possible indentation problems
                                                hit.tail = "\n"
                root.tag = "kwslist"
                del root.attrib["ecf_filename"],root.attrib["language"], root.attrib["encoding"], root.attrib["compareNormalize"], root.attrib["version"]
                root.attrib = OrderedDict([("kwlist_filename","IARPA-babel202b-v1.0d_conv-dev.kwlist.xml"),("language","swahili"),("system_id","")])
                tree.write(path_to_XML_output)