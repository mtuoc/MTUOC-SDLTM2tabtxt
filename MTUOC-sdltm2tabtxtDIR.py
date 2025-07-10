import sys
import sqlite3
import xml.etree.ElementTree as etree
import codecs
import os
import argparse

import html
import re

from ftfy import fix_encoding
import xml.etree.ElementTree as ET



def lreplace(pattern, sub, string):
    """
    Replaces 'pattern' in 'string' with 'sub' if 'pattern' starts 'string'.
    """
    return re.sub('^%s' % pattern, sub, string)

def rreplace(pattern, sub, string):
    """
    Replaces 'pattern' in 'string' with 'sub' if 'pattern' ends 'string'.
    """
    return re.sub('%s$' % pattern, sub, string)
    
def FT2ST(segment):
    segmenttagsimple=segment
    segmenttagsimple=re.sub('(<[^>]+?/>)', "<t/>",segmenttagsimple)
    segmenttagsimple=re.sub('(</[^>]+?>)', "</t>",segmenttagsimple)
    segmenttagsimple=re.sub('(<[^/>]+?>)', "<t>",segmenttagsimple)
    return(segmenttagsimple)
    
def FT2NT(segment):
    segmentnotags=re.sub('(<[^>]+>)', " ",segment)
    segmentnotags=' '.join(segmentnotags.split()).strip()
    return(segmentnotags)
    
def strip_xml_tags(text):
        """
        Removes all XML/HTML-like tags from the input string.

        Args:
            text (str): The input string containing XML tags.

        Returns:
            str: The string with all tags removed.
        """
        return re.sub(r'<[^>]+>', '', text)

def rebuild_segments_with_tags(element_str):
    """
    Reconstruye un segmento SDLTM simplificando las etiquetas a <t> y </t>,
    y unifica múltiples <t> o </t> consecutivas en una sola.
    """
    root = ET.fromstring(element_str)
    parts = []
    open_tags = []

    for elem in root.findall('./*'):
        if elem.tag == 'Text':
            val = elem.findtext('Value', default='')
            parts.append(val)
        elif elem.tag == 'Tag':
            tag_type = elem.findtext('Type')
            if tag_type == 'Start':
                parts.append('<t>')
                open_tags.append('<t>')
            elif tag_type == 'End':
                if open_tags:
                    open_tags.pop()
                parts.append('</t>')

    # Reconstrucción inicial
    result = ''.join(parts).replace('\n', ' ')

    # 🔧 Normalización de etiquetas múltiples consecutivas
    result = re.sub(r'(<t>\s*)+', '<t>', result)       # Varias <t> seguidas → una <t>
    result = re.sub(r'(\s*</t>)+', '</t>', result)     # Varias </t> seguidas → una </t>

    return result

def sdltm2tabtxtDIR(sdltmdir, fsortida):
    sortida=codecs.open(fsortida,"w",encoding="utf-8")
    for root, dirs, files in os.walk(sdltmdir):
        for file in files:
            if file.endswith(".sdltm"):
                try:
                    sdltmfile=os.path.join(root, "", file)
                    print(sdltmfile)
                    conn=sqlite3.connect(sdltmfile)
                    cur = conn.cursor() 
                    cur.execute('select source_segment,target_segment from translation_units;')
                    data=cur.fetchall()
                    for d in data:
                        ssxml=d[0]
                        tsxml=d[1]
                        #try:
                        rootSL = ET.fromstring(ssxml)
                        #for text in rootSL.iter('Value'):
                            #sltext="".join(text.itertext()).replace("\n"," ")
                        rootSL = ET.fromstring(ssxml)
                        sl_value = rootSL.find('.//Elements')
                        
                        sltext = ET.tostring(sl_value, encoding="unicode", method="xml").replace("\n", " ") if sl_value is not None else ""
                        sltext=rebuild_segments_with_tags(sltext)
                        rootTL = ET.fromstring(tsxml)
                        tl_value = rootTL.find('.//Elements')
                        tltext = ET.tostring(tl_value, encoding="unicode", method="xml").replace("\n", " ") if tl_value is not None else ""
                        tltext=rebuild_segments_with_tags(tltext)
                        
                        if not sltext=="" and not tltext=="":
                            if args.noEntities:
                                sltext=html.unescape(sltext)
                                tltext=html.unescape(tltext)
                            if args.simpleTags:
                                sltext=FT2ST(sltext)
                                tltext=FT2ST(tltext)
                            if args.noTags:
                                sltext=FT2NT(sltext)
                                tltext=FT2NT(tltext)
                            if args.fixencoding:
                                sltext=fix_encoding(sltext)
                                tltext=fix_encoding(tltext)
                            cadena=sltext+"\t"+tltext
                            sortida.write(cadena+"\n")
                    
                except:
                    print(sys.exc_info())
                   
    sortida.close()
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='MTUOC program for converting all the SDLTM in a given directory into a tab text.')
    parser.add_argument('-d','--dir', action="store", dest="inputdir", help='The input directory where the SDLTM files are located.',required=True)
    parser.add_argument('-o','--out', action="store", dest="outputfile", help='The output text file.',required=True)    
    parser.add_argument('--noTags', action='store_true', default=False, dest='noTags',help='Removes the internal tags.')
    parser.add_argument('--simpleTags', action='store_true', default=False, dest='simpleTags',help='Replaces tags with <t>, </t> or <t/>.')
    parser.add_argument('--noEntities', action='store_true', default=False, dest='noEntities',help='Replaces html/xml entities by corresponding characters.')
    parser.add_argument('--fixencoding', action='store_true', default=False, dest='fixencoding',help='Tries to restore errors in encoding.')

args = parser.parse_args()
directory=args.inputdir
fsortida=args.outputfile
sdltm2tabtxtDIR(directory, fsortida)

