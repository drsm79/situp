$(function() {
    var pieces = window.location.pathname.split('/_design/');
    // Set database and design doc based on URL
    Backbone.couch.databaseName = pieces[0].replace('/', '');
    Backbone.couch.ddocName  = pieces[1].split('/')[0];
    Backbone.couch.enableChangesFeed = false;

    var Doc = Backbone.Model.extend({
        initialize: function(doc) {  }
    });

    var CollectionFromView = Backbone.Collection.extend({
      // Base class for the other Collection's to use
      model: Doc,
      url: 'highscore',
      stale: "ok",
      initialize: function(settings) {
        // Define the success function in the init so I can have the collection
        // in scope - very hokey...
        var that = this;
        this.success = function(result){
          // Make a list of models to add into the collection
          var models = [];
          _.each( result.rows, function( row ) {
            if(row){
              models.push( that.pullData(row) );
            }
          });
          if ( models.length == 0 ) { models = null }
          return models;
        }
      },
      pullData: function(row){
        // Function to pull out data, override if you want models != rows
        return row;
      },
      error : function(jqXHR, textStatus, errorThrown){
        Backbone.couch.log(["jqXHR", jqXHR]);
        Backbone.couch.log(["textStatus", textStatus]);
        Backbone.couch.log(["errorThrown", errorThrown]);
        return null
      }
    });

    var Games = CollectionFromView.extend({
      doreduce: true,
      group_level: 1,
      group: true,
      pullData: function(row){
        return {name: row.key[0]};
      }
    });

    var Scores = CollectionFromView.extend({
      // Collection of scores, limited to top 10
      doreduce: false,
      descending: true,
      limit: 10,
      pullData: function(row){
        return {player: row.value, score: row.key[1]};
      },
      setGame: function(game){
        // Set the game in the view parameters
        this.startkey = [game, {}];
        this.endkey = [game];
      }
    });

    var GamesView = Backbone.View.extend({
      initialize: function(settings) {
        // Bind functions to actions, store the scores object
        _.bindAll(this);
        this.collection.bind('change', this.render);
        this.collection.bind('add', this.render);
        this.collection.bind('remove', this.render);
        this.collection.bind('reset', this.render);
        this.collection.fetch();
        this.scores = settings.scores;
      },
      render: function() {
        // Define how the collection is rendered into the page
        var dropdown = $('<select></select>');
        var that = this; // needed for the change event below
        this.collection.each(function(game){
          dropdown.append('<option>' + game.get('name') + '</option>');;
        });
        $('.games').html(dropdown);
        this.scores.setGame($('.games select :selected').text());
        // When the dropdown changes set the game for the scores collection,
        // triggering it's render function.
        $('.games select').change(function(event){
          that.scores.setGame($('.games select :selected').text());
        })
      }
    });

    ScoresView = Backbone.View.extend({
      initialize: function(settings) {
        // Bind functions to actions
        _.bindAll(this);
        this.collection.bind('change', this.render);
        this.collection.bind('add', this.render);
        this.collection.bind('remove', this.render);
        this.collection.bind('reset', this.render);
      },
      render: function() {
        // Define how the collection is rendered into the page
        var table = $('<ul></ul>');
        this.collection.each(function(doc){
          table.append('<li>' + doc.get('score') + ' : ' + doc.get('player') + '</li>');
        });
        $('.scores').html('<h2>' + this.game + '</h2>');
        $('.scores').append(table)
      },
      setGame: function(game){
        // Set the game in the view and collection then fetch the collection
        this.game = game;
        this.collection.setGame(game);
        this.collection.fetch();
      }

    });
    // Initialise the app
    var games = new GamesView({
      collection: new Games(),
      scores: new ScoresView({collection: new Scores()})
    });

  }
);