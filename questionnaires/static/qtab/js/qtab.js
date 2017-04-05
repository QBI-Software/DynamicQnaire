 $(document).ready (
     function() {
         var isFirefox = typeof InstallTrigger !== 'undefined';
         var isiPad = navigator.userAgent.match(/iPad/i) != null;
     if (isFirefox && !isiPad) {
         $("input[type='date']").datepicker({dateFormat: 'yy-mm-dd'});
     }
    }
 );

$( "td.coloredbox :input:radio" ).click(function() {
        var choice = $(this).parent().text();
        var color = $( this ).parent().parent().css( "opacity" );
        $( "#msg" ).text( "You selected: " + choice );
        $("td.coloredbox").css("opacity",0.6);
        $( this ).parent().parent().css( "opacity",1.0 );
        /*.show().fadeOut( 1000 );*/

});
var selected = [];

$( "td.coloredbox :input:checkbox" ).click(function() {
        var choice = $(this).val();
        var color = $( this ).parent().parent().css( "opacity" );
        var data = $("#msg" ).text();
        var arr = data.split(':');
        if ($(this).prop('checked')){
            selected.push(choice);
            $( this ).parent().parent().css( "opacity",1.0 );
        }else{
            selected.splice( $.inArray(choice, selected), 1 );
            $( this ).parent().parent().css( "opacity",0.6);
        }
        $( "#msg" ).text( "You selected: " + selected.toString()  );

        /*.show().fadeOut( 1000 );*/

});

$( "td.coloredbox_sm :input:radio" ).click(function(event) {
        var choice = $(this).parent().text();
        var color = $( this ).parent().parent().css( "opacity" );
        var inputid = event.target.id;
        $( "#msg" ).text( "You selected: " + choice );
        $( "#msg-" + inputid ).text( "You selected: " + choice );
        $("td.coloredbox").css("opacity",0.6);
        $( this ).parent().parent().css( "opacity",1.0 );
        /*.show().fadeOut( 1000 );*/

});


$( "td.coloredbox_sm :input:checkbox" ).click(function() {
        var choice = $(this).val();
        var color = $( this ).parent().parent().css( "opacity" );
        var data = $("#msg" ).text();
        var arr = data.split(':');
        if ($(this).prop('checked')){
            selected.push(choice);
            $( this ).parent().parent().css( "opacity",1.0 );
        }else{
            selected.splice( $.inArray(choice, selected), 1 );
            $( this ).parent().parent().css( "opacity",0.6);
        }
        $( "#msg" ).text( "You selected: " + selected.toString()  );

        /*.show().fadeOut( 1000 );*/

});

/* currently within each page as needed
$( ".sliderparams" ).each(function( index ) {
    var spid = "#" + sp.id;
    var minrange = parseInt($(spid).attr("rmin"));
    var num = parseInt($(spid).attr("numoptions"));
    var selectid = "#" + spid.attr("selectid");
    var select = $(selectid);
    var sliderid = "#slider-" + $(spid.attr("counter"));


    $( sliderid ).slider({
        range:"min",
        min: minrange,
        max: num,
        value: select[ 0 ].selectedIndex + 1,
        slide: function( event, ui ) {
          select[ 0 ].selectedIndex = ui.value - 1;
        }
    });
    select.on( "change", function() {
          $( sliderid ).slider( "value", this.selectedIndex + 1 );
        });
    });

    */

/*Specific Ladder question */
$("#ladderquestion").parent().removeClass("table-responsive");