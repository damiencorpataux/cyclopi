/*

Pour la gravure:

- Cut:
  - Speed: 20 mm/s
  - Power min/max: 60/60 %

- Scan (with mode: Swing)
  - Speed: 100 mm/s
  - Power min/max: 35/35 %

*/

$fn = 120;

margin = 0.2;
pitch = 2.54;
led_size = 5 + margin;  // FIXME: Apply margin later in the code, case by case !
square_n_leds = 5;
ring_radius = 32;  // from ring center to led center
ring_n_leds = 24;

module Square(
    pitch = pitch,
    led_size = led_size,
    n = square_n_leds
) {
    for ( x = [0 : 4] ){
        for ( y = [0 : 4] ){
            translate([x*(led_size+pitch), y*(led_size+pitch), 0])
            cube([led_size, led_size, 1]);
        }
    }
}

module Circle(
    led_size = led_size,
    radius = ring_radius,
    n = ring_n_leds
) {
    for(a=[0:360/n:360]) {
        r = radius;
        translate([-r*sin(a), +r*cos(a), 0]) {
            rotate([0,0,a]) {
                translate([0, 0, 0])
                cube([led_size, led_size, 1], center=true);
            }
        }
    }
}

module LEDs() {
    offset = ((square_n_leds-1)*pitch + square_n_leds*led_size) / 2;
    translate([-offset, -offset, 0])
    Square();
    Circle();
}

projection(cut=true)
translate([0,0,-0.5])
difference() {
    cylinder(1, r=36);
    LEDs();
}
