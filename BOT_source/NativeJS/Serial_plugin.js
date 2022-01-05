// Load support for logging straight to logcat here
const BotShell = require('/data/data/com.ohmnilabs.telebot_rtc/files/assets/node-files/bot_shell');
const LogCatter = require('logcatter');
const Log = new LogCatter('Turn_off_Serial');

class offserialSPlugin {

  constructor(botnode) {
    this._botnode = botnode;
    var self = this;
    Log.i("  -> Serial_plugin loaded!");

    // Bind some extra bot shell commands
    BotShell.prototype.cmd_serial = function(parts) {
      if(String(parts) == "off")
      {
        this.log(" Running off serial" );
        // delete this._botnode._serial._sport;
        // this._botnode._serial._opened = false;
        this._botnode._serial._sport.close(function (err) {
          cthis.log('port closed', err);
      });

      }
      else if (String(parts) =="on")
      {
        this.log(" Running On serial" );
        setTimeout(function () {
          self.botnode_._serial.createSerial();
        }, 100);
      }
      else{
        this.log("Unkowncmd! Using serial on/off" );
      }
    }
  }
}

// IMPORTANT - do not forget this line to export the class
module.exports = offserialSPlugin;


// function MyPLugin(botnode) {
//   var self = this;
//   this.botnode_ = botnode;
//   console.log("MyPLugin loaded")

//   //Switch to use tb_control serial,
//   //by turning off the tb-node’s serial port
//   delete this.botnode_._serial._sport;
//   this.botnode_._serial._opened = false;

//   setTimeout(function () {
//     //When you want to use the tb-node’s serial port,
//     //turn off the tb_control or calling the disconnect service.
//     //Then, reconnect tb-node serial port
//     self.botnode_._serial.createSerial();
//   }, 5000);
// }
// module.exports = MyPLugin;
