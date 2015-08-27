#!/usr/bin/env python

# Alpha for Summoners War

from gimpfu import *;
from array import array;
from random import randint;
from math import sqrt;

def rgb_to_hsv(r, g, b):
    # All this code was plagiarized. No ragrets. Tom Lehrer.
    r = float(r / 255.0);
    g = float(g / 255.0);
    b = float(b / 255.0);
    minRGB = min(r, min(g, b));
    maxRGB = max(r, max(g, b));
    if (minRGB == maxRGB):
        return 0, 0, int(minRGB * 100);
    d = g - b if r == minRGB else (r - g if b == minRGB else b - r);
    h = 3 if r == minRGB else (1 if b == minRGB else 5);
    h = 60.0 * (h - d / (maxRGB - minRGB));
    s = (maxRGB - minRGB) / maxRGB * 100.0;
    v = maxRGB * 100.0;
    return int(h), int(s), int(v);

def rgb_to_lab(r, g, b):
    # Convert to XYZ: 2 Degrees, D65
    r = float(r / 255.0);
    g = float(g / 255.0);
    b = float(b / 255.0);
    if (r > 0.04045):
        r = ((r + 0.055) / 1.055) ** 2.4;
    else:
        r = r / 12.92;
    if (g > 0.04045):
        g = ((g + 0.055) / 1.055) ** 2.4;
    else:
        g = g / 12.92;
    if (b > 0.04045):
        b = ((b + 0.055) / 1.055) ** 2.4;
    else:
        b = b / 12.92;
    r = r * 100.0;
    g = g * 100.0;
    b = b * 100.0;
    x = r * 0.4124 + g * 0.3576 + b * 0.1805;
    y = r * 0.2126 + g * 0.7152 + b * 0.0722;
    z = r * 0.0193 + g * 0.1192 + b * 0.9505;
    # Convert to Lab: Same Settings
    x = x / 95.047;
    y = y / 100.000;
    z = z / 108.883;
    if (x > 0.008856):
        x = x ** (1.0/3.0);
    else:
        x = x * 7.787 + 16.0 / 116.0;
    if (y > 0.008856):
        y = y ** (1.0/3.0);
    else:
        y = y * 7.787 + 16.0 / 116.0;
    if (z > 0.008856):
        z = z ** (1.0/3.0);
    else:
        z = z * 7.787 + 16.0 / 116.0;
    cie_l = (116.0 * y) - 16.0;
    cie_a = 500.0 * (x - y);
    cie_b = 200.0 * (y - z);
    return cie_l, cie_a, cie_b;

def delta_e(l1, a1, b1, l2, a2, b2): # CIE76 Color Difference Formula
    return sqrt((l2 - l1) ** 2.0 + (a2 - a1) ** 2.0 + (b2 - b1) ** 2.0);

# This is my own, sh*tty code.

def h_difference(h1, h2):
    large = max(h1, h2);
    small = min(h1, h2);
    return min((large - small), (small + 360 - large));

def sv_difference(sv1, sv2):
    return abs(sv1 - sv2);

def hsv_tolerant(h1, s1, v1, h2, s2, v2, tolh, tols, tolv):
    h_diff = h_difference(h1, h2);
    s_diff = sv_difference(s1, s2);
    v_diff = sv_difference(v1, v2);
    return h_diff < tolh and s_diff < tols and v_diff < tolv;

def lab_tolerant(r1, g1, b1, r2, g2, b2, tol_lab):
    l1, a1, b1 = rgb_to_lab(r1, g1, b1);
    l2, a2, b2 = rgb_to_lab(r2, g2, b2);
    return delta_e(l1, a1, b1, l2, a2, b2) < tol_lab;

def sw_alpha_layer(img, layer, trans_color, tol_lab, tolh, tols, tolv, contained, con_factor):
    # Fun Message :D ("Clearing Background (" + str(trans_color[0]) + ", " + str(trans_color[1]) + ", " + str(trans_color[2]) + ")...")
    blurbs = ["Summoning Mystical Scroll...", "Handing Out Arena Invitations...", "Toad Poisoning Rina...",
    "Defeating Kiyan...", "Passively Converting Magic...", "Browsing Monster Galleries...",
    "Dubbing Darion 'Knight'...", "Gz-ing 5* nat Summoners...", "Clearing Faimon Volcano...",
    "Eternally Reviving Perna...", "Evolving 6* Monsters...", "Searching for Light SDs...",
    "Dealing DoTs...", "Fusing Sig, Kat, and Vero...", "Refreshing Magic Shop..."];
    gimp.progress_init(blurbs[randint(0, len(blurbs) - 1)]);

    pdb.gimp_layer_add_alpha(layer); # Begin by adding alpha (transparency) layer.


    # Initialize Variables

    # Layer Stats
    w = layer.width; # Image Width
    h = layer.height; # Image Height
    total = float(w * h); # Total amount of pixels.
    counter = 0.0; # Progress Counter
    # Border Control
    allowed = [not contained] * (w * h); # Array of Booleans
    changed = 1 if contained else 0;
    compass = [[-1, -1], [0, -1], [1, -1], [-1, 0], [1, 0], [-1, 1], [0, 1], [1, 1]];
    # Color Values
    transr, transg, transb = trans_color[:3]; # I swear this is one of the few times I can get away with a :3 face in code.
    transh, transs, transv = rgb_to_hsv(transr, transg, transb);

    # Joao Bueno's Pixel Region tricks make everything lightning fast...
    srcRgn = layer.get_pixel_rgn(0, 0, w, h, False, False); # Get Pixel Regions
    dstRgn = layer.get_pixel_rgn(0, 0, w, h, True, True); # Get Pixel Regions
    p_size = len(dstRgn[0,0]); # Length of Char Array in One Pixel (RGBA is 4)
    dest_pixels = array("B", srcRgn[0:w, 0:h]); # Convert to Unsigned Char Array
    clear = array("B", [0] * p_size); # Assuming p_size will be 4 (RGBA) but I'm taking no prisoners.
    
    # New Layer for Color to Alpha
    ca_layer = gimp.Layer(img, "SW CA Temp " + layer.name, w, h, layer.type, layer.opacity, layer.mode);
    ca_region = ca_layer.get_pixel_rgn(0, 0, w, h, True, True); # Get Pixel Region of CA Layer
    ca_transfer = array("B", [0] * (w * h * p_size)); # Blank Unsigned Char Array
    img.add_layer(ca_layer, 0);



    # Loops

    reverse = False; # This may or may not lower the O time taken by these loops.
    while changed > 0: # Border Control Loop
        changed = 0;
        for x in range(0, w):
            for y in (range(h - 1, -1, -1) if reverse else range(0, h)):
                apos = (x + y * w);
                pos = apos * p_size;
                test = dest_pixels[pos: pos + p_size]; # Get Array of Pixel at Pos

                r, g, b = test[:3]; # Another cat face.
                h1, s1, v1 = rgb_to_hsv(r, g, b); # Convert to hsv.

                if (not allowed[apos] and ((r == transr and g == transg and b == transb) or lab_tolerant(r, g, b, transr, transg, transb, tol_lab * con_factor))):
                    allowed[apos] = True;
                    changed += 1;
                elif (not allowed[apos] and hsv_tolerant(h1, s1, v1, transh, transs, transv, tolh, tols, tolv) and lab_tolerant(r, g, b, transr, transg, transb, tol_lab)):
                    for dir in compass:
                        npos = x + dir[0] + (y + dir[1]) * w;
                        if (npos >= 0 and npos < w * h):
                            if (allowed[npos]):
                                allowed[apos] = True;
                                changed += 1;
                                break;

                counter += 1;
                prog = float(counter / total);
                if (int(prog * 100) % 5 == 0):
                    gimp.progress_update(prog);
        gimp.progress_init(blurbs[randint(0, len(blurbs) - 1)]);
        counter = 0;

    for x in range(0, w): # Pixel Copier Loop
        for y in range(0, h):
            pos = (x + y * w) * p_size;
            test = dest_pixels[pos: pos + p_size]; # Get Array of Pixel at Pos

            r, g, b = test[:3]; # Yet another cat face.
            h1, s1, v1 = rgb_to_hsv(r, g, b); # Convert to hsv.

            if (r == transr and g == transg and b == transb):
                test = clear;
            elif (allowed[x + y * w] and hsv_tolerant(h1, s1, v1, transh, transs, transv, tolh, tols, tolv) and lab_tolerant(r, g, b, transr, transg, transb, tol_lab)):
                ca_transfer[pos: pos + p_size] = test;
                test = clear;
                # Probably will do something else here too.

            dest_pixels[pos: pos + p_size] = test;
            counter += 1;
            prog = float(counter / total);
            if (int(prog * 100) % 5 == 0):
                gimp.progress_update(prog);

    dstRgn[0:w, 0:h] = dest_pixels.tostring();
    ca_region[0:w, 0:h] = ca_transfer.tostring();

    layer.flush(); # Forces Bitstream??? idk
    layer.merge_shadow(True); # No idea here too.
    layer.update(0, 0, w, h); # Update Image

    ca_layer.flush(); # Forces Bitstream??? idk
    ca_layer.merge_shadow(True); # No idea here too.
    ca_layer.update(0, 0, w, h); # Update Image

    pdb.plug_in_colortoalpha(img, ca_layer, trans_color);
    pdb.gimp_image_merge_visible_layers(img, 0);

    

def sw_alpha(img, s_layer, trans_color, all_layers, tol_lab, tolh, tols, tolv, contained, con_factor):
    pdb.gimp_image_undo_group_start(img); # Pre-operation Undo

    layers = [];
    # Get visible layers.
    for i in img.layers:
        if ((not all_layers and s_layer == i) or not i.visible):
            continue;
        layers.append(i);
        i.visible = False;

    if (all_layers):
        final = [];
        while (len(layers) > 0):
            layer = layers.pop(0);
            layer.visible = True;
            sw_alpha_layer(img, layer, trans_color, tol_lab, tolh, tols, tolv, contained, con_factor);
            for i in img.layers:
                if (i.visible):
                    final.append(i);
                    i.visible = False;
        for i in final:
            i.visible = True;
    else:
        sw_alpha_layer(img, s_layer, trans_color, tol_lab, tolh, tols, tolv, contained, con_factor);
        for i in layers:
            i.visible = True;

    pdb.gimp_image_undo_group_end(img); # Post-operation Redo

register(
    "python_fu_sw_alpha",
    "Clear the background in a monster picture",
    "Clear the background in a monster picture",
    "Cappycot",
    "Chris Wang",
    "2015",
    "<Image>/Colors/SWAlphaColor(py)...",
    "*",
    [
    (PF_COLOR, "Color", "Color to clear", (56.0 / 255.0, 34.0 / 255.0, 18.0 / 255.0)),
    (PF_BOOL, "bool", "Alpha all visible layers? (Y/N, obviously.)", True),
    (PF_SPINNER, "tolerance", "Main Tolerance (CIE76)", 100.0, (0.5, 200.0, 0.5)),
    (PF_SLIDER, "hue", "Hue Tolerance", 270, (0, 360, 1)),
    (PF_SLIDER, "saturation", "Sat Tolerance", 75, (0, 100, 1)),
    (PF_SLIDER, "value", "Val Tolerance", 75, (0, 100, 1)),
    (PF_BOOL, "bool", "Source Contained (Border control, not recommended.)", False),
    (PF_SLIDER, "factor", "Source Factor", 0.5, (0, 1, 0.01)),
    ],
    [],
    sw_alpha);

main();
