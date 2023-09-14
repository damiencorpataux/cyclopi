/*
FIXME:
- Correct the height of connector hole in the Case()
- Correct the height of the Base()
- Fix un-faceted cylinder to go till the bottom of the Base()
*/

$fn = 120;

// FIXME: Fix margin computation: apply in code case by case, not in arguments...

margin = 0.2;
inner_diameter = 72 + margin;  // LED Ring width = 72.00
croptop_border = 1;
croptop_height = 1.5;

connector_module_width = 9.9;
connector_module_height = 4.3;

height_to_ledboard = 5.1 + croptop_height;
height_to_connector = 14 + croptop_height - connector_module_height;
height_to_protoboard = 15.5 + croptop_height;
height_to_mcu = 22.25 + croptop_height;

acrylic_to_connector = 13.5;
acrylic_and_leds = 5.3;  // height
electronic_protoboard = 0;
electronic_top = 0;
electronic_module = 17.4;  // height without acrylic_and_leds ?


screw_diameter = 4.4;  // M5 effective diameter: 4.2-4.5
screw_height = 7;  // centered, from case top height
strapholder_height = 12;
strapholder_depth = 4;

case_border = 6;
case_height = height_to_mcu + case_border + margin;
case_plughole_height = height_to_connector;

echo("Case height:", case_height);
echo("acrylic_to_connector", acrylic_to_connector);
echo("height_to_connector", height_to_connector);

module Case(
    height = case_height,
    diameter = inner_diameter,  // inner diameter
    border = case_border,
    croptop_border = croptop_border,
    croptop_height = croptop_border,
    plughole_width = connector_module_width - margin,
    plughole_height = case_plughole_height,
    strapholder_height = strapholder_height,
    strapholder_depth = strapholder_depth
) {
    difference() {
        union() {
            // Border
            difference() {
                // Case border
                cylinder(
                    h = height,
                    d = diameter+border,
                    center = false);
                // Case hollow
                cylinder(
                    h = height+border,
                    d = diameter,
                    center = false);
            }
            // Top crop
            difference() {
                cylinder(
                    h = croptop_height,
                    d = diameter+border,
                    center = false);
                cylinder(
                    h = croptop_height,
                    d = diameter-croptop_border,
                    center = false);
            }
        }
        // Connector hole
        translate([-plughole_width/2, -diameter/2-border, plughole_height]) {
            #cube([plughole_width, border*2, height-plughole_height]);
        }
        // Screw hole
        translate([-diameter/2, 0, height-screw_height]) {
            rotate([0, 90, 0]) {
                #cylinder(
                    h = border*2,
                    d = screw_diameter,
                    center = true);
            }
        }
    }
    Drop(
         height = height,
         diameter = inner_diameter,  // inner diameter
         border = case_border,
         strapholder_height = strapholder_height,
         strapholder_depth = strapholder_depth   
    );
}

base_height = case_height - height_to_mcu;
base_plughole_height = case_height - case_plughole_height - connector_module_height;
module Base(
    diameter = inner_diameter - margin,  // inner diameter
    border = 3,
    height = base_height,
    screw_height = screw_height,
    screw_diameter = screw_diameter,
    plughole_width = connector_module_width,
    plughole_height = base_plughole_height,
    strapholder_depth = strapholder_depth,
    strapholder_height = base_plughole_height-3,
    strapholder_offset = 2
) {
    difference() {
        union() {
            // Base and hole
                difference() {
                    cylinder(
                        h = height,
                        d = diameter,
                        center = false);
                translate([0, 0, border]) {
                    cylinder(
                        h = height,
                        d = diameter-border,
                        center = false);
                }
            }
            // Screw pad
            translate([diameter/2-border, -screw_diameter, 0]) {
                cube([border, screw_diameter*2, screw_diameter*2.25]);
            }
            // Connector hole (filler), FIXME: make it round using intersection()
            translate([-plughole_width/2, -diameter/2-strapholder_offset, 0]) {
                cube([plughole_width, border+strapholder_offset, plughole_height]);
            }
            // Strap holder
            translate([-plughole_width/2, -diameter/2-strapholder_depth-strapholder_offset, 0]) {
                difference() {
                    cube([plughole_width, strapholder_depth, strapholder_height]);
                    translate([0, strapholder_depth/2, strapholder_depth/2]) {
                        #cube([plughole_width, strapholder_depth/2, strapholder_height-strapholder_depth]);
                    }
                }
            }
        }
        // Screw hole
        translate([diameter/2-border/2, 0, screw_height]) {
            rotate([0, 90, 0]) {
                #cylinder(
                    h = border*2,
                    d = screw_diameter,
                    center = true);
            }
        }
    }    
}

module Drop(
    height = case_height,
    diameter = inner_diameter,  // inner diameter
    border = case_border,
    strapholder_height = strapholder_height,
    strapholder_depth = strapholder_depth
) {
    difference() {
        hull() {
            // Case border
            cylinder(
                h = height,
                d = diameter+border,
                center = false);
            // Water-drop (FIXME)
            drop_size_x = 10;
            drop_size_y = 10;
            drop_size_z = 10;
            translate([0,50,10]) {
                rotate([-90,0,0]) {
                    cylinder(20, 10, 3);
                }
            }
        }
        // Strap hole (in waterdrop)
        translate([0, 42, 1]) {
            translate([-strapholder_height/2, 0, -height/2]) {
                #cube([strapholder_height, strapholder_depth, height*2]);
            }
            translate([-diameter/2, 0, height/2-strapholder_height/2-2.2]) {  // FIXME: -10/4 is empirical
                #cube([diameter, strapholder_depth, strapholder_height]);
            }
        }
        // Remove case border cylinder, used for hull()
        cylinder(
            h = height,
            d = diameter+border,
            center = false);
    }
}


// Print plate

offset = inner_diameter/2+case_border/2;

translate([-offset, 0, 0]) {
    Case();
}
translate([+offset, 0, 0]) {
    Base();
}
