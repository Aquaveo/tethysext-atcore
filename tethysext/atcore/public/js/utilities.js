/*****************************************************************************
 * FILE:    utilities.js
 * DATE:    October, 19, 2018
 * AUTHOR:  Nathan Swain
 * COPYRIGHT: (c) Aquaveo 2018
 * LICENSE:
 *****************************************************************************/
function contains(str, sub) {
    if (str.indexOf(sub) === -1) {
        return false;
    }
    return true;
}

function in_array(item, array) {
    return array.indexOf(item) !== -1;
}

function is_defined(variable) {
    return !!(typeof variable !== typeof undefined && variable !== false);
}

function to_title_case(str) {
    return str.replace(/\w+/g, function(txt){return txt.charAt(0).toUpperCase() + txt.substr(1).toLowerCase();});
};

function var_to_title_case(str) {
    str = str.replace(/_/ig, ' ');
    return to_title_case(str);
};

function compute_center(features) {
    let sum_x = 0,
        sum_y = 0,
        num_coordinates = 0;

    for (var i = 0; i < features.length; i++) {
        let feature = features[i], geometry;

        // If feature is a ol.Feature, we need to get the geometry
        if (feature instanceof ol.Feature) {
            geometry = feature.getGeometry();
        }
        // If feature is a geometry already
        else if (feature instanceof ol.geom.Geometry) {
            geometry = feature;
        }
        // Otherwise skip this "feature"
        else {
            continue;
        }

        // Get the geometry and sum up x's and y's
        let geometry_type = geometry.getType();

        if (geometry_type == 'Point') {
            let coordinate = geometry.getCoordinates();
            sum_x += coordinate[0];
            sum_y += coordinate[1];
            num_coordinates += 1;
        }
        else if (geometry_type == 'LineString'){
            let coordinates = geometry.getCoordinates();
            for (var i = 0; i < coordinates.length; i++) {
                let coordinate = coordinates[i];
                sum_x += coordinate[0];
                sum_y += coordinate[1];
                num_coordinates += 1;
            }
        }
        else if (geometry_type == 'Polygon') {
            let line_strings = geometry.getCoordinates();
            for (var i = 0; i < line_strings.length; i++) {
                let line_string = line_strings[i];

                for (var j = 0; j < line_string.length; j++) {
                    let coordinate = line_string[j];
                    sum_x += coordinate[0];
                    sum_y += coordinate[1];
                    num_coordinates += 1;
                }
            }
        }
    }

    // Return null if no coordinates found
    if (num_coordinates <= 0) {
        return null;
    }

    let center_coordinates = [ sum_x / num_coordinates, sum_y / num_coordinates];
    return new ol.geom.Point(center_coordinates);
};