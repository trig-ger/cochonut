"""
Parser

"""

from xml.etree import ElementTree
from lxml import etree

VERBOSE = False

def get_note_data(note_elem):
    '''
    Retrieve data about a note from a MusicXML note-element
    '''

    #print 'Getting note_data for:\n', ElementTree.dump(note_elem)

    note_data = {'isChord': False}

    chord_elem = note_elem.find('chord')
    if chord_elem is not None:
        note_data['isChord'] = True

    pitch_elem = note_elem.find('pitch')
    if pitch_elem is not None:
        note_data['type'] = 'pitch'

        step_elem = pitch_elem.find('step')
        if step_elem is not None:
            note_data['p_step'] = step_elem.text

        octave_elem = pitch_elem.find('octave')
        if octave_elem is not None:
            note_data['p_octave'] = int(octave_elem.text)

        alter_elem = pitch_elem.find('alter')
        if alter_elem is not None:
            note_data['p_alt'] = int(alter_elem.text)

    unpitch_elem = note_elem.find('unpitched')
    if unpitch_elem is not None:
        note_data['type'] = 'unpitched'

    rest_elem = note_elem.find('rest')
    if rest_elem is not None:
        note_data['type'] = 'rest'

    dur_elem = note_elem.find('duration')
    if dur_elem is not None:
        note_data['duration'] = int(dur_elem.text)

    return note_data

def get_part_list(tree):
    part_list = []
    parts = tree.find('part-list')
    for score_part in parts.findall('score-part'):
        id = score_part.attrib['id']
        name = score_part.find('part-name').text
        part = {'id': id, 'name': name, 'div': '', 'next_interval': 0}
        part_list.append(part)
    return part_list

def get_part(part_list, part_id):
    '''
    Find a part with a given id in the list of parts
    '''
    for part in part_list:
        if part['id'] == part_id:
            return part
    return None

def get_part_div(part_list, id):
    for part in part_list:
        if part['id'] == id:
            return part['div']
    return None

def set_part_div(part_list, id, div):
    #myLogger.info('Setting divisions for part ' + id + ' to ' + str(div))
    for part in part_list:
        if part['id'] == id:
            part['div'] = div


def find_largest_div(tree):
    '''
    Find the largest divisor in the entire score. Used to specifiy the length
    of intervals that are the length of the shortest note in the score.
    '''
    largest_divisor = 1
    divisions = tree.findall('measure/part/attributes/divisions')
    for d in divisions:
        div = int(d.text)
        if div > largest_divisor:
            largest_divisor = div
            #myLogger.info('Found new largest divisor: ' + str(largest_divisor))

    return largest_divisor

def store_rest(intervals, start, length):
    for i in range(start,start+length):
        if i+1 > len(intervals):
            intervals.append({'attacks': 0, 'pitches': []})

def store_pitch(intervals,pitch, start, length):
    """
    Store a pitch in the list of intervals. The pitch will start at
    interval 'start' and last start+length intervals
    """
    #print start
    
    for i in range(start,start+length):
        if i+1 > len(intervals):
            intervals.append({'attacks': 0, 'pitches': []})
        intervals[i]['pitches'].append(pitch)
        
    intervals[start]['attacks'] = intervals[start]['attacks'] + 1
    #print str(intervals[start])




def parse_file(file, pitch_classes):
    """
    Parse a file of the MusicXML format.
    
    """

    #global myLogger
    #myLogger = logger

    #myLogger.info('Parsing ' + file)
    if VERBOSE:
        print 'Parsing', file

    # parse file to a xml-tree datastructure
    #tree = ElementTree.parse(file)
    docFile = open(file, 'r')
    doc = etree.parse(docFile)
    docroot = doc.getroot()

    # check if we need to convert to time-wise format
    if docroot.tag == 'score-partwise':
        #myLogger.info('Found part_elem-wise score, converting to time-wise')
        xsltFileName = '../xslt_stylesheets/parttime.xsl'
        xsltFile = open(xsltFileName, 'r')
        xsltDoc = etree.parse(xsltFile)
        transform = etree.XSLT(xsltDoc)
        tree = transform(doc)
    elif docroot.tag == 'score-timewise':
        #myLogger.info('Found time-wise score')
        tree = doc
    else:
        error = 'Provided file is not MusicXML'
        #myLogger.error(error)
        raise Exception(error)

    # TODO: Below: Consistent looping through children: either by using find() or getchildren()

    # the minimal segments that will be returned
    mini_segments = []

    intervals = []


    # get the list of parts that the score consists of
    part_list = get_part_list(tree)
    #myLogger.info('Found part_elem-list: ' + str(part_list))
    if VERBOSE:
        print 'Found part_elem-list: ', str(part_list)

    # the current interval
    #current = 0
    current_interval = 0

    # find largest divisor
    #myLogger.info("Searching for largest divisor")
    largest_divisor = find_largest_div(tree)
    #myLogger.info("Shortest note is 1/" + str(4*largest_divisor))
    if VERBOSE:
        print "Shortest note is 1/" + str(4*largest_divisor)

    # current divisor    
    #current_div = largest_divisor

    # iterate through file
    measures = tree.findall('measure')
    for measure in measures:
        #print 'measure', measure.attrib['number']
        parts = measure.findall('part')
        #ElementTree.dump(measure)

        # the minimal segments within the measure
        #measureMSegments = []

        for part_elem in parts:

            # get id of part
            part_id = part_elem.attrib['id']
            if VERBOSE:
                print '------------part ' + part_elem.attrib['id'] + '-------------'
            part = get_part(part_list, part_id)
            next_interval = part['next_interval']
            if VERBOSE:
                print 'Next interval in this part: ', next_interval

            #---- attributes ----#

            att_elem = part_elem.find('attributes')

            if att_elem is not None:
                divisions = att_elem.find('divisions')
                if divisions is not None:
                    #current_div = int(divisions.text)
                    set_part_div(part_list, part_id, int(divisions.text))


            #---- pitches ----#

            p_children = part_elem.getchildren()
            for p_child in p_children:

                #---- note ----#

                if p_child.tag == 'note':
                    note_data = get_note_data(p_child)

                    # TODO: handle grace notes with no duration
                    duration = 0
                    if note_data.has_key('duration'):
                        duration = note_data['duration']
                    #print 'duration:', duration
                    
                    # retrieve current divisor in this part
                    current_div = get_part_div(part_list, part_id)
                    
                    # how long is a quater note?
                    quater_part = duration / float(current_div)
                    #print 'quater_part:', quater_part
                    
                    # length is ???
                    length = int(quater_part * largest_divisor)
                    
                        
                    # TODO: handle rests (have next/current intervals for measures/parts)
                    if note_data['type'] == 'rest':
                        #current_interval = next_interval                                
                        #next_interval = current_interval + length
                        
                        #print 'Found rest with length', length
                        store_rest(intervals, next_interval, length)
                        if VERBOSE:
                            print "Added rest from " + str(next_interval) + " to " \
                            + str(next_interval+length-1)
                        next_interval = next_interval + length
                        
                        
                        
                    elif note_data['type'] == 'pitch':
                        #print 'Found pitch'

                        #print 'len', len(mini_segments)
                        #print 'current', current
                        #print 'current_interval', current_interval

                        # find length in terms of intervals
                        #print 'current_div', current_div
                        
                        #duration = 0
                        #if note_data.has_key('duration'):
                        #    duration = note_data['duration']
                        #print 'duration:', duration
                        #quater_part = duration / float(current_div)
                        #print 'quater_part:', quater_part
                        #length = int(quater_part * largest_divisor)
                        #print 'length:', length

                        if note_data['isChord']:
                            pass
                            #print 'Chord note'
                        else:
                            #print "Non-chord note"
                            # the note is not a chord, so the interval that we
                            # place the note in is the next one
                            current_interval = next_interval                                
                            next_interval = current_interval + length                        
                        
                        # pitch alternation
                        alt = 0
                        if note_data.has_key('p_alt'):
                            alt = note_data['p_alt']
                        
                        # pitch (class + octave)
                        # TODO: Support quater-tone sharp?
                        p_class = (pitch_classes[note_data['p_step']] + alt) % 12
                        pitch = {'pitch_class': p_class, 'octave': note_data['p_octave']}
                                
                        # store in intervals list
                        # TODO: handle grace notes with no duration
                        if duration > 0:
                            store_pitch(intervals, pitch, current_interval, length)
                            if VERBOSE:
                                print "Added " + str(pitch) + ' from ' + \
                                str(current_interval) + ' to ' + \
                                str(current_interval+length-1)


                #---- forward/backup ----#

                if p_child.tag == 'forward':
                    duration_elem = p_child.find('duration')
                    duration = int(duration_elem.text)
                    current_div = get_part_div(part_list, part_id)
                    quater_part = duration / float(current_div)
                    length = int(quater_part * largest_divisor)
                    next_interval = next_interval + length
                    
                    if VERBOSE:
                        print 'Forward with length ' + str(length)
                    
                    #if note_data.has_key('duration'):
                    #    duration = note_data['duration']
                    #print 'duration:', duration
                    
                    #print 'quater_part:', quater_part
                    
                    #print 'length:', length
                    #current_div = part['div']

                    #print 'duration:', duration.text
                    #print 'div:', current_div

                if p_child.tag == 'backup':
                    duration_elem = p_child.find('duration')
                    duration = int(duration_elem.text)
                    current_div = get_part_div(part_list, part_id)
                    quater_part = duration / float(current_div)
                    length = int(quater_part * largest_divisor)
                    next_interval = next_interval - length
                    
                    if VERBOSE:
                        print 'Backup with length ' + str(length)
                    #print 'quater_part:',quater_part
                    #print 'largest_divisor:', largest_divisor
                    #print 'div:', current_div
                    #current_div = part['div']
                    
            part['next_interval'] = next_interval

    shortestNote = 4 * largest_divisor
    #myLogger.info('Done parsing, now returning')
    
    #print str(intervals[12])
    
    #return shortestNote, mini_segments
    return largest_divisor, intervals

#---- end of parse_file ----#

#------- unused code  ------#

#    # set current divider
                #    part['div'] = div

                #    # check if this is largest divider
                #    if div > largest_divisions:
                #        largest_divisions = div
                #        myLogger.info('Found new largest divisions element: ' + str(largest_divisions))

                
                #key = att_elem.find('key')
                #if key is not None:
                #    #print 'key:'
                #    fifths = key.find('fifths')
                #    #print 'fifths:', fifths.text
                #
                #    mode = key.find('mode')
                #    if mode is not None:
                #        #print 'mode:', mode.text
                #        pass
                
#if len(mini_segments) >= current + 1:
                            #    # a minimal segment already exists
                            #    pass

                            #else:
                            #    # no minimal segment; create one
                            #    print 'Creating mini seg'


                                #mini_seg = {'attacks': 1, 'length': 0, 'pitches': []}
                                #mini_segments.append(mini_seg)
                                
                                #mini_segments[current]['pitches'] = []
                                #mini_segments[current]['pitches'].append(pitch)
                                #current = current + 1

                                #next_interval = 
                                
# 
                            #current = current - 1
                            
                            # pitch
                            #alt = 0
                            #if note_data.has_key('p_alt'):
                            #    alt = note_data['p_alt']
                            #p_class = get_pitch_class(note_data['p_step'], alt)
                            #pitch = {'pitch': p_class, 'octave': note_data['p_octave']}
                                
                            # store in intervals list
                            #for i in range(current_interval,current_interval+length):
                            #    if i+1 > len(intervals):
                            #        intervals.append([])
                            #    intervals[i].append(pitch)
                            #    
                            #print "Added " + str(pitch) + ' from ' + str(current_interval) + ' to ' + str(current_interval+length)
                            
                            # increment no. of attacks 
                            #a = mini_segments[current]['attacks']
                            #a = a + 1
                            #mini_segments[current]['attacks'] = a
                            
                            #mini_segments[current]['pitches'].append(pitch)
                            #current = current + 1
