import xml.etree.ElementTree as ET
import numpy as np
from collections import OrderedDict
import copy



class Hit():
        """
        Represents a hit from a query
        - self.scores is a dictionary which contains the score
        for each of the system that has recognized this hit
        (example: self.scores = {"System1":0.5, "System2":0.6}) 
        - We overload the __eq__ function so that two hits are considered equal
        if their intervals overlap by more than 30% of the shortest of the two
        - self.combine_hits combine two hits: the resulting hit will have the basic
        characteristics of the hit that contained the highest score in its self.scores,
        and the new self.scores is the union of the self.scores of the two hits
        - self.combined_score takes as argument a dictionary that specifies the 
        MTWV of each of the system for which it has a score in self.scores, 
        and computes the combined score out of self.scores using the methodology 
        provided as its second argument
        """
        def __init__(self, info, scores):
                self.file_name = info[0]
                self.channel_name = info[1]
                self.tbeg = float(info[2])
                self.tdur = float(info[3])

                self.scores = scores

        def __eq__(self,other_Hit):
                i = [self.tbeg,other_Hit.tbeg].index( min([self.tbeg,other_Hit.tbeg]) )
                intersection = max(0,[self.tbeg+self.tdur,other_Hit.tbeg+other_Hit.tdur][i]-[self.tbeg,other_Hit.tbeg][1-i])
                return (intersection>0.3*min(self.tdur,other_Hit.tdur) and self.channel_name == other_Hit.channel_name and self.file_name == other_Hit.file_name)
        
        def __hash__(self):
                return hash((self.file_name,self.channel_name))
        
        def combine_hits(self, other_Hit):
                if max(self.scores.values())>= max(other_Hit.scores.values()):
                        combined_hit = copy.deepcopy(self)
                        combined_hit.scores.update(other_Hit.scores)
                else:
                        combined_hit = copy.deepcopy(other_Hit)
                        combined_hit.scores.update(self.scores)
                return combined_hit


        def get_kw_element(self,systems_MTWV,combination_methodology):
                kw= ET.Element("kw")
                score = self.combined_score(systems_MTWV,combination_methodology)
                kw.attrib = {"file": self.file_name, "channel":self.channel_name, "tbeg": str(np.round(self.tbeg,2)), "dur":str(np.round(self.tdur,2)), "score":str(np.round(score,6)), "decision": "YES"}
                kw.tail = "\n"+ 2*"  "
                return kw

        def combined_score(self, systems_MTWV,combination_methodology):
                combined_score = 0
                sum_of_MTWV = sum([systems_MTWV[system] for system in systems_MTWV])
                max_of_MTWV = max([systems_MTWV[system] for system in systems_MTWV])
                for system_name, system_MTWV in systems_MTWV.items():
                        if system_name in self.scores:
                                if combination_methodology == "CombSUM":
                                        combined_score +=  self.scores[system_name] 
                                        
                                elif combination_methodology == "CombMNZ":
                                        combined_score += ( len(self.scores) * self.scores[system_name] )

                                elif combination_methodology == "WCombMNZ":
                                        combined_score += len(self.scores) * (system_MTWV / sum_of_MTWV) * self.scores[system_name]

                                elif combination_methodology == "Power2":
                                        combined_score +=  2**(system_MTWV - max_of_MTWV) * self.scores[system_name]
                return combined_score
        


class System_Combiner():
        """
        self.merge_XML_lists_of_hits_files takes as argument:
        - a list of (paths to) XML lists of hits that it must merge
        - the path to the new merged XML list
        - a list of the names of the systems associated to each XML list of hits
        - the MTWV of each of these systems (in a dictionary)
        - the methodology with which to merge the scores

        The hits are stored as instances of the class Hit
        For each query, it uses self.merge_list_of_hits to create a single list
        out of all the hits associated to that query (from all systems),
        and merge the hits when necessary using the methods from the Hit class
        """
        def __init__(self):
                self.systems = []
                self.systems_MTWV = dict()

        def merge_XML_lists_of_hits_files(self,list_of_paths_to_XML_files,path_to_output_merged_XML_file, list_of_systems_names,dict_of_systems_MTWV,combination_methodology):
                self.systems = list_of_systems_names
                self.systems_MTWV = dict_of_systems_MTWV
                new_tree = copy.deepcopy(ET.parse(list_of_paths_to_XML_files[0]))
                new_root = new_tree.getroot()
                root_dict = dict()
                for index, system_name in enumerate(self.systems):
                        root_dict[system_name] = ET.parse(list_of_paths_to_XML_files[index]).getroot()
                for detected_kwlist in new_root:
                        for kw in list(detected_kwlist):
                                detected_kwlist.remove(kw)
                        kwid = detected_kwlist.attrib["kwid"]
                        list_of_hits = []
                        for system, root in root_dict.items():
                                for query in root:
                                        if query.attrib["kwid"] == kwid:
                                                for kw in query:
                                                        info=[kw.attrib["file"],kw.attrib["channel"], kw.attrib["tbeg"],kw.attrib["dur"]]                                                 
                                                        list_of_hits.append(Hit(info,{system: float(kw.attrib["score"])}))
                        merged_list_of_hits = self.merge_list_of_hits(list_of_hits)
                        for hit in merged_list_of_hits:
                                detected_kwlist.append(hit.get_kw_element(self.systems_MTWV,combination_methodology))
                new_tree.write(path_to_output_merged_XML_file)
        
        def merge_list_of_hits(self,list_of_hits):
                merged_list = dict()
                for hit in list_of_hits:
                        # We use the overloaded __eq__ function of the Hit class
                        if hit in merged_list:
                                merged_list[hit] = hit.combine_hits(merged_list[hit])
                        else:
                                merged_list[hit] = hit
                return [merged_list[hit] for hit in merged_list]
        
        