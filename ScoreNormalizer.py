import xml.etree.ElementTree as ET
import numpy as np
from collections import OrderedDict
from Index import Speech_entity



def Normalize_score(path_to_input_XML_list_of_hits,path_to_output_XML_list_of_hits, normalization_method = "STO", alpha = 1, T = 10*60*60, beta = 999.9):
        """
        Opens an XML file that contains a list of KWS hits, and performs (depending on the normalization_method argument) either
        - "STO": Sum-To-One normalization of the scores (with parameter alpha>0)
        - "KST": Keyword-specific thresholding (with parameter alpha>0, total duration T (in seconds), and weight beta)
        - "QL": Query length normalization
        Outputs the result in a new XML file
        """
        tree=ET.parse(path_to_input_XML_list_of_hits)
        root = tree.getroot()
        for detected_kwlist in root:
                if len(detected_kwlist) != 0: 
                        if normalization_method == "STO":
                                scores=np.array([float(kw.attrib["score"]) for kw in detected_kwlist])
                                normalization_factor =  np.sum(scores**alpha)+10**(-6)
                                for  kw in detected_kwlist :
                                        kw.attrib["score"]= str(np.round( float(kw.attrib["score"])**alpha / normalization_factor , 6))
                        elif normalization_method == "KST":
                                posterior_sum = np.sum( np.array ([float(kw.attrib["score"]) for kw in detected_kwlist])  )
                                log_kw_specific_tresh = np.log( beta * alpha * posterior_sum/(T+ (beta - 1)*alpha * posterior_sum) )
                                for  kw in detected_kwlist :
                                        kw.attrib["score"]= str( np.round( float(kw.attrib["score"])**(-1/log_kw_specific_tresh) ,6))
                        elif normalization_method == "QL":
                                average_duration = np.mean( np.array ([float(kw.attrib["dur"]) for kw in detected_kwlist])  ) + 10**(-6)
                                for  kw in detected_kwlist :
                                        kw.attrib["score"]= str( np.round( float(kw.attrib["score"])**(1/average_duration) ,6))
                        else:
                                print("Choose valid normalization method")
        tree.write(path_to_output_XML_list_of_hits)


