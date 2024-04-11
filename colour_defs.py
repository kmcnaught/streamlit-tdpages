def make_case_insensitive(dictionary):
    all_vals = {}
    for k, v in dictionary.items():
        all_vals[k.upper()]= v
        all_vals[k.lower()]= v
    for k, v in all_vals.items():
        dictionary[k]=v
        
        
def get_letter_colours_symbols():
    # These were manually retrieved from an example pageset in TD Snap
    # Each number represents the symbol ID within TD Snap for a symbol displaying a capital letter
    letter_symbols = {
        "a": 701, 
        "b": 704, 
        "c": 706, 
        "d": 708, 
        "e": 710, 
        "f": 712, 
        "g": 714, 
        "h": 716, 
        "i": 12814, 
        "j": 720, 
        "k": 722, 
        "l": 724, 
        "m": 726, 
        "n": 728, 
        "o": 730, 
        "p": 732, 
        "q": 734, 
        "r": 736, 
        "s": 738, 
        "t": 740, 
        "u": 742, 
        "v": 744, 
        "w": 746, 
        "x": 748, 
        "y": 750, 
        "z": 752
    }

    cols = {
        "blue1":-1643526,
        "blue2":-1314057,
        "blue3":-3085583,
        "blue4":-1640198,
        "blue5":-1643526,
        "blue6":-3085583,
        "red1":-1343567,
        "red2":-333592,
        "red3":-201735,
        "red4":-10005,
        "red5":-1591854,
        "red6":-201735,
        "red7":(250,150,150),
        "sand6":-1130620,
        "white2":-132102,
        "green1":-3019575,
        "green2":-1049887,
        "green3":-1639702,
        "sand1":-925488,
        "sand2":-329242,
        "sand3":-4681,
        "sand4":-133215,
        "sand5":-11695,
        "white1":-328966,
    }

    # Groups, with minor variants within each group

    # Plosives/Bilabial & Alveolar Stops (P, B, T, D)
    # K and G Sounds (K, C, G, Q) 
    # Fricatives (F, V, S, Z, X) 
    # Affricates and Sharp Consonant Blends (CH, J, SH) 
    # Liquids (L, R) 
    # Nasals (M, N)
    # H and W Sounds (H, W, WH) 
    # Y Sound (Y) 

    vowels = "sand4"   # Vowels (A, E, I, O, U)
    pbtd = "blue5"     # Plosives/Bilabial & Alveolar Stops (P, B, T, D)
    kg = "green2"      # K and G Sounds (K, C, G, Q) 
    fric = "red5"     # Fricatives (F, V, S, Z, X) 
    j = "sand5"      # Affricates and Sharp Consonant Blends (CH, J, SH) 
    liquid = "red7"    # Liquids (L, R) 
    m = "green1"      # Nasals (M, N)
    n = "blue6"        # Nasals (M, N)
    wh = "white1"      # H and W Sounds (H, W, WH) 
    y = "sand4"       # Y Sound (Y) 

    letter_colors = {
        'A': cols[vowels],
        'B': cols[pbtd],
        'C': cols[kg],
        #'CH': cols[j],
        'D': cols[pbtd],
        'E': cols[vowels],
        'F': cols[fric],
        'G': cols[kg],
        'H': cols[wh],
        'I': cols[vowels],
        'J': cols[j],
        'K': cols[kg],
        'L': cols[liquid],
        'M': cols[m],
        'N': cols[n],
        'O': cols[vowels],
        'P': cols[pbtd],
        'Q': cols[kg],
        'R': cols[liquid],
        'S': cols[fric],
        #'SH': cols[j],
        'T': cols[pbtd],
        'U': cols[vowels],
        'V': cols[fric],
        'W': cols[wh],
        'X': cols[fric],
        'Y': cols[y],
        'Z': cols[fric],
    }

    # we want to support both upper and lower case keys
    make_case_insensitive(letter_colors)
    make_case_insensitive(letter_symbols)
    
    return (letter_colors, letter_symbols)


