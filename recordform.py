import sys
sys.path.append( '..' )

import datetime
import json
import kivy
from kivy.adapters.dictadapter import DictAdapter
from kivy.adapters.listadapter import ListAdapter
from kivy.app import App
from kivy.atlas import Atlas
from kivy.cache import Cache
from kivy.lang import Builder
from kivy.properties import *
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.checkbox import CheckBox
from kivy.uix.dropdown import DropDown
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.listview import ListItemButton, ListView
from kivy.uix.popup import Popup
from kivy.uix.selectableview import SelectableView
from kivy.uix.scrollview import ScrollView
from kivy.uix.stacklayout import StackLayout
from kivy.uix.textinput import TextInput

import random

from api.lineup import *
from commons.foos import *
import commons.visibility_conditions as vconds
import commons.strings.ita as strings

from kivyextras.foos import *
from kivyextras.flatui import PopupComboBox
from kivyextras.flatui import FlatTextInput
from kivyextras.flatui import FlatButton
from kivyextras.flatui import FloatingAction

Builder.load_file( 'forms/recordform.kv' )

class RecordForm( BoxLayout ) :

    mainArea    = ObjectProperty( None )
    class_name  = StringProperty( None )
    data        = ObjectProperty( None )
    metadata    = ListProperty( [] )
    fields      = ListProperty( [] )

    font_name   = StringProperty( 'font/Roboto-Light.ttf' )
    font_size   = NumericProperty( 20 )
    row_height  = NumericProperty( 40 )

    def __init__( self, **kargs ) :
        super( RecordForm, self ).__init__( orientation="vertical", **kargs ) 
        self.fields = sorted( map( lambda o:o['field_name'], self.metadata ) )
        self._row_padding = 9
        self._buildFormRows()

    """
    Commit changes.
    """
    def commit( self ) :
        result = self.data.commit()

    """
    Builds all the fields of the form.
    """
    def _buildFormRows( self ) : 

        for field in self.fields :
                    
            self._field = field
            metas = filter( lambda o:o['field_name']==field, self.metadata )
            self._meta = list( metas )[0] 
            conditions = eval( self._meta[ 'conditions' ] )

            if conditions( self.data ) :

                self._descriptor = self._getFieldDescriptor()
                self._value = self.data[ field ] if field in self.data.keys() else None

                if self._field.startswith( 'rif' ) :
                    relateds = run_query( self._descriptor['class'] )
                    row = self._buildRelationshipRow( field, relateds )
                else :
                    row = self._buildDataRow( field )

                self.mainArea.add_widget( row )
                self.mainArea.height += row.height

    """
    Prepares all the information needed to render the field.
    """
    def _getFieldDescriptor( self ) :

        table_name = class_name = ''

        if self._field.startswith( 'rif' ) :
            table_name = self._meta['table2_name'] 
            class_name = table2class_name( table_name )

        return {    
            'type'   : self._meta[ 'field_type' ], \
            'pytype' : python_type( self._meta['field_type'] ), \
            'lang'   : self._meta[ strings.LANG ], \
            'hint'   : self._meta[ strings.HINT ], \
            'iskey'  : self._field.startswith( 'rif' ), \
            'table'  : table_name, \
            'class'  : class_name
        }

    """
    Build row for data field.
    """
    def _buildDataRow( self, field ) : 

        row = BoxLayout( height=self.row_height )
        row.add_widget( self._fieldHeader( field ) )
        row.add_widget( self._fieldValue( field ) )
        row.add_widget( self._dummyFieldActions() )
        return row

    """
    Build row for relationship field.
    """
    def _buildRelationshipRow( self, field, relateds ) : 

        #Popup
        mainbutton = PopupComboBox( 
            font_size  = self.font_size,
            font_name  = self.font_name,
            list_data  = relateds, 
            color      = ( .17, .17, .17, 1 ), 
            popup_args = { 
                'size_hint'  : ( 1.1, 0.6 ),
                'title'      : strings.pick_a_record,
                'title_size' : self.font_size * 1.5
            },
            on_selection = lambda o: self.data.__setitem__( field, o.selected['rowid'] )
        ) 

        #Standard actions
        fieldActions = BoxLayout( size_hint=(0.15, 1), spacing=5 )
        btn1 = FlatButton( text='...', font_name=self.font_name, font_size=self.font_size )
        btn2 = FlatButton( icon='images/search-32.png', font_name=self.font_name, font_size=self.font_size )
        fieldActions.add_widget( btn1 )
        fieldActions.add_widget( btn2 )

        #Popup button
        temp = list( filter( lambda r:r['rowid'] == self._value, relateds ) )
        if len( temp ) > 0 : 
            related = temp[0]
            mainbutton.select( relateds.index( related ) )
        else :
            mainbutton.text = strings.no_records_available

        #Row layout
        x = BoxLayout( size_hint=(0.4, 1) )
        x.add_widget( mainbutton )
        row = BoxLayout( height=self.row_height )
        row.add_widget( self._fieldHeader( field ) )
        row.add_widget( x )
        row.add_widget( Label(size_hint=(0.1,1)) )
        row.add_widget( fieldActions )
        return row

    """
    Builds field header layout object.
    """
    def _fieldHeader( self, field ) :
        fieldHeader = BoxLayout( size_hint=(0.35, 1) )
        fieldLabel = Label( 
            text= self._descriptor['lang'], size_hint=(None,None), color=(0,0,0,1), \
            font_name=self.font_name, font_size=self.font_size 
        )
        y = 0 if field.startswith('rif') else self.font_size/2.1
        fieldLabel.bind( texture_size=lambda l,s: l.setter('size')(l,[s[0],self.row_height+y]) )
        fieldHeader.add_widget( fieldLabel )
        return fieldHeader

    """
    Build the best layout basing on the field type.
    """
    def _fieldValue( self, field ) :

        x = StackLayout( size_hint=( 0.5, 1 ) )
        kind = self._descriptor['pytype']

        if kind == str or kind == int or kind == float :

            value = str( self._value ) if self._value is not None else ''  
            p = ( self._descriptor['type'] == 'password' )
            c = FlatTextInput( 
                text=value, hint_text=self._descriptor['hint'], \
                multiline=False, password=p, \
                font_size=self.font_size, font_name=self.font_name
            )
            c.bind( text=lambda l,v: self.data.__setitem__(field,v) )
            x.add_widget( c )

        if kind == bool :

            value = bool( self._value )
            c = CheckBox( size_hint=( 0.05, 1 ), active=value )
            c.bind( active=lambda l,v: self.data.__setitem__(field,v) )
            b = BoxLayout( size_hint=( 0.85, 1 ) )
            x.add_widget( c )
            x.add_widget( b )
        return x

    """
    Build dummy buttons.
    """
    def _dummyFieldActions( self ) :
        fieldActions = BoxLayout( size_hint=(0.15, 1), spacing=5 )
        btn1 = FlatButton( text='...', font_name=self.font_name, font_size=self.font_size )
        fieldActions.add_widget( btn1 )
        return fieldActions

