odoo.define('tis_hr_attendance_geolocalize.geo_location_finder', function (require) {
    "use strict";
    var lat=[];
    var long=[];

    const attendance = require('hr_attendance.my_attendances');
    attendance.include({
        update_attendance(){
            var self = this;
            if (navigator.geolocation) {
                navigator.geolocation.watchPosition(showPosition);
              } else {
                alert("Geolocation is not supported by this browser.")
              }
            function showPosition(position) {
                  lat=position.coords.latitude
                  long=position.coords.longitude
            }

            var emp_latitude=lat;
            var emp_longitude=long;
            this._rpc({
                model: 'hr.employee',
                method: 'attendance_fetch',
                args: [[self.employee.id], 'hr_attendance.hr_attendance_action_my_attendances', null, [emp_latitude, emp_longitude]],
            })
            .then(function(result) {
                if (result.action) {
                    self.do_action(result.action);
                } else if (result.warning) {
                    self.displayNotification({ title: result.warning, type: 'danger' });
                }
            });
        },
    });

});