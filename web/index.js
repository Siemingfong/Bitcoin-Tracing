var MongoClient = require('mongodb').MongoClient;
var url = "mongodb://bitcoin_tracing:bt2018@localhost:27017/BT" 

var express = require('express');
var app = express();
var http = require('http');
http.createServer(app).listen(8877);

app.use(express.static('public'));

app.get('/', function (req, res) {
    res.sendFile(__dirname + '/public/html/index.html');
});


app.get('/find', function (req, res) {
    address = req.query.address;
    MongoClient.connect(url, function(err, db) {
        if (err) throw err;
        
        var dbo = db.db("BT");
        
        collect = dbo.collection("mixer");
        
        collect.find({address: address}).toArray(function(err, result) {
            if (err) throw err;
            db.close();
            if (result.length != 0){
                ans = result[0]
                res.send({
                    type:'mixer',
                    data:ans
                });
            }
            else{
                MongoClient.connect(url, function(err, db) {
                    if (err) throw err;
        
                    var dbo = db.db("BT");

                    collect = dbo.collection("tager");
                    collect.find({address: address}).toArray(function(err, result) {
                        if (err) throw err;
                        db.close();
                        if (result.length != 0){
                            ans = result[0]
                            res.send({
                                type:'tager',
                                data:ans
                            });
                        }
                        else{
                            res.send({
                                type:'unknown'
                            });
                        }
                    });
                });
            }
        });
        
    });
});