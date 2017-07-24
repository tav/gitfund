# Public Domain (-) 2015-2017 The GitFund Authors.
# See the GitFund UNLICENSE file for details.

fs = require('fs')
path = require('path')
qs = require('querystring')

SVG_DIR = path.join(path.dirname(process.cwd()), 'private', 'mvp', 'svg')

getSVG = (name) ->
  data = fs.readFileSync path.join(SVG_DIR, name + '.svg'), {encoding: "utf-8"}
  data = qs.escape(data)
    .replace(/%0A/g, '')
    .replace(/%20/g, ' ')
    .replace(/%22/g, "'")
    .replace(/%3A/g, ':')
    .replace(/%3D/g, '=')
    .replace(/%2F/g, '/')
  'url("data:image/svg+xml,' + data + '")'

svgColours = (svg, bg, fg) ->
  svg.replace(/FOREGROUND/g, qs.escape(fg))
     .replace(/BACKGROUND/g, qs.escape(bg))

FOOTER_ICON_COLOUR = '#a7b2b8'
LINK_COLOUR = '#0c90c9'

EMAIL_SVG = getSVG('email')
EMAIL_WHITE = svgColours(EMAIL_SVG, 'transparent', '#fff')

FACEBOOK_COLOUR = '#3b5998'
FACEBOOK_SVG = getSVG('facebook')
FACEBOOK_FOOTER = svgColours(FACEBOOK_SVG, 'transparent', FOOTER_ICON_COLOUR)
FACEBOOK_WHITE = svgColours(FACEBOOK_SVG, 'transparent', '#fff')

GITHUB_COLOUR = '#171515'
GITHUB_SVG = getSVG('github')
GITHUB_BLACK = svgColours(GITHUB_SVG, '', GITHUB_COLOUR)
GITHUB_STAR = getSVG('github-star')
GITHUB_STAR_BLACK = svgColours(GITHUB_STAR, '', GITHUB_COLOUR)

LINKEDIN_COLOUR = '#0077b5'
LINKEDIN_SVG = getSVG('linkedin')
LINKEDIN_ICON = svgColours(LINKEDIN_SVG, LINKEDIN_COLOUR, '#fff')

MENU_SVG = getSVG('menu')

TWITTER_COLOUR = '#1da1f3'
TWITTER_SVG = getSVG('twitter')
TWITTER_FOOTER = svgColours(TWITTER_SVG, 'transparent', FOOTER_ICON_COLOUR)
TWITTER_ICON = svgColours(TWITTER_SVG, 'transparent', TWITTER_COLOUR)
TWITTER_WHITE = svgColours(TWITTER_SVG, 'transparent', '#fff')

module.exports = (api) ->

  api.add

    html:
      boxSizing: 'border-box'
      height: '100%'
      margin: 0
      padding: 0

    '*, *:before, *:after':
      boxSizing: 'inherit'

    body:
      background: '#fff'
      display: 'table'
      fontFamily: '"Open Sans", sans-serif'
      fontSize: '16px'
      fontWeight: 400
      height: '100%'
      lineHeight: '27px'
      margin: 0
      minHeight: '100vh'
      padding: 0
      width: '100%'

    a:
      color: LINK_COLOUR
      textDecoration: 'none'
      img:
        border: 'none'
      '&:hover':
        textDecoration: 'none'

    code:
      fontFamily: '"Source Code Pro", monospace'
      fontSize: '15px'
      fontWeight: '400'
      background: '#f5f5f5'
      borderLeft: '2px solid #fff'
      borderRight: '2px solid #fff'
      padding: '3px 6px'

    h1:
      color: '#232d32'
      fontSize: '24px'
      fontWeight: '400'
      lineHeight: '34px'
      margin: '22px 0 24px 0'

    h2:
      color: '#232d32'
      fontSize: '20px'
      fontWeight: '400'

    h3:
      fontSize: '24px'
      fontWeight: 400
      lineHeight: '36px'
      marginTop: '20px'
      marginBottom: '0px'

    label:
      cursor: 'pointer'

    p:
      marginTop: '1em'

    pre:
      backgroundColor: '#fefefe'
      border: '1px solid #c4c6c2'
      borderLeft: '5px solid #c4c6c2'
      color: '#101010'
      fontFamily: '"Source Code Pro", monospace'
      fontSize: '15px'
      fontWeight: '400'
      lineHeight: '24px'
      overflow: 'auto'
      padding: '12px 15px 13px 12px'
      margin: '20px 30px 0 20px'
      borderBottomRightRadius: '12px'

    table:
      width: '100%'

    '.alert-blue, .alert-green, .alert-red':
      padding: '10px 13px'
      marginBottom: '20px'
      textAlign: 'center'
      a:
        color: '#000'
        textDecoration: 'underline'
        '&:hover':
          textDecoration: 'none'

    '.alert-blue':
      background: '#62b3e5'
      color: '#fff'

    '.alert-green':
      background: '#dff0d8'

    '.alert-red':
      background: '#ffc788'

    '.backers':
      listStyleType: 'none'
      margin: '0 0 20px 0'
      padding: '0'
      li:
        border: '1px solid #fff'
        float: 'left'
        padding: '20px'
        textAlign: 'center'
        width: '25%'
        overflow: 'hidden'
        '@media all and (max-width: 720px)':
          width: '33%'
        '@media all and (max-width: 500px)':
          width: '50%'
        '@media all and (max-width: 400px)':
          float: 'none'
          width: '100%'
          maxWidth: '240px'
          margin: '0 auto'
        'div':
          color: '#2a2a2a'
          fontSize: '14px'
          overflow: 'hidden'
          whiteSpace: 'nowrap'
        img:
          padding: '3px'
          border: '1px solid #dadada'
          borderRadius: '50%'
          width: '100%'
        '&:hover':
          border: '1px dotted #dadada'

    '.backing-plan-backers':
      color: '#a7b2b8'
      fontSize: '13px'
      lineHeight: '13px'
      paddingTop: '1px'

    '.backing-plan-disabled':
      cursor: 'default'
      pointerEvents: 'none'
      a:
        background: '#efefef !important'
        border: '1px solid #cacaca !important'
        color: '#000 !important'

    '.backing-plan-select':
      textAlign: 'center'
      a:
        background: '#2bde73'
        borderRadius: '3px'
        color: '#fff'
        display: 'inline-block'
        padding: '8px 16px'
        marginBottom: '14px'
        transition: 'background-color 250ms ease-out'
        '&:hover':
          background: '#1fc863'

    '.backing-plan-title':
      color: '#232d32'
      fontWeight: '700'
      paddingTop: '10px'

    '.body':
      background: '#fff'
      clear: 'both'

    '.campaign':
      background: '#fff'

    '.campaign-banner':
      background: '#ecf0f1'
      padding: '24px 0 18px 0'
      '.sponsor':
        background: '#2bde73'
        borderRadius: '5px'
        color: '#fff'
        float: 'right'
        fontSize: '24px'
        lineHeight: '24px'
        fontWeight: '400'
        minWidth: '280px'
        padding: '15px 20px'
        textAlign: 'center'
        transition: 'background-color 250ms ease-out'
        '&:hover':
          background: '#1fc863'
        '&:active':
          background: '#1fc863'
        '@media all and (max-width: 800px)':
          display: 'block'
          float: 'none'
          marginTop: '5px'
          width: '100%'
      '.info':
        color: '#79858b'
        display: 'inline-block'
        fontSize: '18px'
        lineHeight: '24px'
        padding: '15px 60px 15px 0'
        '@media all and (max-width: 800px)':
          padding: '5px 15px 15px 0'
        a:
          color: 'inherit'
          fontWeight: 'inherit'
          textDecoration: 'none'
          '&:hover':
            textDecoration: 'none'
        strong:
          color: '#232d32'
          fontSize: '24px'
          paddingRight: '3px'

    '.campaign-box':
      marginBottom: '20px'

    '.campaign-box-divider':
      borderBottom: '1px solid #e8eced'
      marginBottom: '10px'
      paddingBottom: '10px'

    '.campaign-box-inner':
      padding: '10px 16px'

    '.campaign-box-inner-sides':
      padding: '0px 16px'

    '.campaign-box-title':
      color: '#41484c'
      fontSize: '14px'
      fontWeight: '400'
      padding: '5px 16px'

    '.campaign-cols':
      marginTop: '20px'

    '.campaign-col1':
      float: 'left'
      width: '590px'
      '@media all and (max-width: 922px)':
        float: 'none'
        width: '100%'

    '.campaign-col2':
      float: 'right'
      width: '280px'
      '@media all and (max-width: 922px)':
        float: 'none'
        width: '100%'

    '.campaign-content':
      '.full-bleed':
        lineHeight: '0px'
        marginLeft: '-18px'
        marginRight: '-18px'
        img:
          width: '100%'

    '.campaign-inner':
      margin: '0 auto'
      width: '900px'
      '@media all and (max-width: 922px)':
        margin: '0'
        width: '100%'

    '.card-details':
      marginBottom: '30px'

    '.card-icons':
      display: 'inline-block'
      marginLeft: '10px'
      img:
        marginRight: '3px'
        position: 'relative'
        top: '8px'
        height: '30px'
      '@media all and (max-width: 922px)':
        display: 'block'
        marginLeft: '0'
        marginTop: '5px'

    '.card-secure':
      color: '#acacac'
      display: 'inline-block'
      fontSize: '14px'
      paddingLeft: '14px'
      position: 'relative'
      top: '-3px'
      img:
        marginRight: '1px'
        position: 'relative'
        top: '-1px'
        verticalAlign: 'middle'
        width: '18px'

    '.center':
      textAlign: 'center'

    '.clear':
      clear: 'both'

    '.comment-link':
      '&:hover':
        textDecoration: 'underline'

    '.community-page':
      padding: '40px 0 24px 0'

    '.content':
      color: '#232323'
      fontSize: '17px'
      fontWeight: '400'
      lineHeight: '30px'
      a:
        textDecoration: 'underline'
        color: LINK_COLOUR
        '&:hover':
          textDecoration: 'none'
      table:
        border: '1px solid #efefef'
        borderCollapse: 'collapse'
        marginTop: '15px'
      thead:
        background: '#efefef'
      tbody:
        tr:
          borderTop: '1px solid #efefef'
      th:
        fontWeight: 'normal'
        padding: '5px 8px'
      td:
        fontSize: '15px'
        padding: '5px 8px'

    '.cursor':
      margin: '20px 0 40px 0'
      textAlign: 'center'

    '.dataform':
      paddingBottom: '60px'
      '@media all and (max-width: 922px)':
        paddingBottom: '30px'
      'input[type=submit]':
        '-webkit-appearance': 'none'
        background: '#2bde73'
        border: '0'
        color: '#fff'
        cursor: 'pointer'
        display: 'block'
        fontSize: '20px'
        outline: '0'
        width: '300px'
        '&:active':
          background: '#1fc863'
        '@media all and (max-width: 922px)':
          width: '100%'
      'input':
        border: '1px solid #ccc'
        fontSize: '16px'
        fontWeight: '300'
        marginBottom: '10px'
        padding: '15px 10px'
        '@media all and (max-width: 922px)':
          marginBottom: '0'
      'input[type=file]':
        border: '0px'
        padding: '15px 0px 0px 0px'
      'input.field-cvc':
        width: '70px'
      'input.field-input':
        width: '300px'
        '@media all and (max-width: 922px)':
          width: '100%'
      'input.field-disabled':
        border: '1px solid #fff'
      'select':
        fontSize: '16px'
        fontWeight: '300'
        marginRight: '10px'
      'label':
        display: 'inline-block'
        float: 'left'
        fontWeight: 400
        paddingTop: '10px'
        textAlign: 'right'
        width: '200px'
        '@media all and (max-width: 922px)':
          display: 'block'
          float: 'none'
          paddingTop: '0px'
          textAlign: 'left'
          width: '100%'
          '&:after':
            content: '":"'
      '.field':
        clear: 'both'
        paddingBottom: '40px'
        '@media all and (max-width: 922px)':
          paddingBottom: '0'
      '.field-data':
        float: 'left'
        marginLeft: '30px'
        marginBottom: '25px'
        '@media all and (max-width: 922px)':
          float: 'none'
          margin: '0'
          padding: '20px'
      '.field-errmsg':
        color: 'red'
        display: 'none'
        fontWeight: 300
        '@media all and (max-width: 922px)':
          paddingTop: '12px'
      '.field-submit':
        clear: 'both'
        marginLeft: '230px'
        '@media all and (max-width: 922px)':
          marginLeft: '0px'
          paddingTop: '10px'
        p:
          marginTop: '0px'
          paddingTop: '0px'
          '@media all and (max-width: 922px)':
            p:
              paddingBottom: '10px'
      '.field-error':
        'label':
          color: 'red'
        'input':
          background: '#fee'
          border: '1px solid red'
        '.field-errmsg':
          display: 'block'

    '.disqus':
      padding: '20px 0'
      '@media all and (max-width: 922px)':
        borderBottom: '1px solid #e7e9ee'
        marginBottom: '20px'

    '.e':
      width: '1.2em'
      height: '1.2em'
      position: 'relative'
      top: '3px'

    '.fix-layout':
      fontSize: '1px'
      lineHeight: '1px'

    '.float-right':
      float: 'right'

    '.footer':
      background: '#232d32'
      color: '#fff'
      display: 'table-row'
      fontWeight: '300'

    '.footer-content':
      padding: '50px 0 20px 0'

      ul:
        listStyleType: 'none'
        display: 'inline-block'
        margin: '0 90px 50px 0'
        padding: '0px'
        verticalAlign: 'top'
        li:
          padding: '5px 0'
        a:
          color: '#a7b2b8'
          textDecoration: 'none'
          '&:hover':
            color: '#fff'

    '.footer-facebook':
      background: "#{FACEBOOK_FOOTER} no-repeat"
      paddingLeft: '25px'

    '.footer-twitter':
      background: "#{TWITTER_FOOTER} no-repeat"
      paddingLeft: '25px'

    '.form':
      'input[type=text], input[type=password]':
        fontSize: '16px'
      'input[type=submit]':
        '-webkit-appearance': 'none'
        background: '#2bde73'
        border: '0'
        color: '#fff'
        cursor: 'pointer'
        fontSize: '20px'
        outline: '0'
        '&:active':
          background: '#1fc863'
      'input[type=file]':
        border: '0px'
        padding: '15px 0px'
      'input':
        border: '1px solid #ccc'
        display: 'block'
        fontWeight: '300'
        width: '350px'
        padding: '15px 10px'
        margin: '20px auto 0 auto'
        textAlign: 'center'
        '@media all and (max-width: 450px)':
          margin: '20px 0 0 0'
          width: '100%'

    # GitHub button adapted from:
    # http://codepen.io/desandro/pen/meKVrM
    '.ghb':
      color: '#333'
      height: '20px'
      fontFamily: '"Helvetica Neue", Arial, sans-serif'
      fontSize: '15px'
      fontWeight: 'bold'
      lineHeight: '20px'
      marginRight: '4px'
      '.ghb-left':
        border: '1px solid #e5e5e5'
        padding: '6px 10px 6px 10px'
      '.ghb-right':
        border: '1px solid #e5e5e5'
        borderLeft: '0px solid #e5e5e5'
        padding: '6px 10px 6px 9px'
      '&:hover':
        '.ghb-left':
          backgroundColor: '#fafafa'

    '.ghb-icon':
      background: "#{GITHUB_BLACK} no-repeat"
      display: 'inline-block'
      height: '20px'
      position: 'relative'
      marginRight: '6px'
      top: '4px'
      width: '20px'

    '.ghb-star':
      background: "#{GITHUB_STAR_BLACK} no-repeat"
      display: 'inline-block'
      height: '20px'
      position: 'relative'
      marginRight: '4px'
      top: '4px'
      width: '20px'

    '.goal-bar':
      background: '#f2f4f5'
      borderRadius: '3px'
      height: '8px'
      marginTop: '12px'
      div:
        background: '#2bde73'
        borderRadius: '3px'
        height: '8px'

    '.goal-period':
      color: '#a7b2b8'
      fontSize: '13px'
      lineHeight: '13px'
      paddingTop: '2px'

    '.goal-status':
      fontWeight: '700'
      paddingTop: '18px'
      span:
        fontSize: '14px'
        fontStyle: 'italic'
        fontWeight: '300'

    '.header':
      background: '#fff'
      height: '82px'
      paddingTop: '15px'

    '.button-facebook':
      background: '#4267b2'
      border: '1px solid #4267b2'
      borderRadius: '3px'
      color: '#fff'
      padding: '5px 12px 5px 8px'
      fontFamily: '"Helvetica Neue", Arial, sans-serif'
      fontWeight: 500
      lineHeight: '20px'
      marginRight: '4px'
      '&:hover':
        background: '#34518d'
        border: '1px solid #34518d'
      span:
        background: "#{FACEBOOK_WHITE} no-repeat"
        display: 'inline-block'
        paddingLeft: '24px'

    '.button-twitter':
      background: '#1b95e0'
      border: '1px solid #1b95e0'
      borderRadius: '3px'
      color: '#fff'
      padding: '5px 12px 5px 8px'
      fontFamily: '"Helvetica Neue", Arial, sans-serif'
      fontWeight: 500
      lineHeight: '20px'
      marginRight: '4px'
      '&:hover':
        background: '#0c7abf'
        border: '1px solid #0c7abf'
      span:
        background: "#{TWITTER_WHITE} no-repeat"
        display: 'inline-block'
        paddingLeft: '24px'

    '.image':
      width: '100%'

    '.imglink':
      borderBottom: '0px !important'

    '.inner':
      margin: '0 auto'
      width: '900px'
      '@media all and (max-width: 922px)':
        padding: '0 15px'
        margin: '0'
        width: '100%'

    '.inner-pad-only':
      '@media all and (max-width: 922px)':
        padding: '0 15px'

    '.irc-info':
      marginTop: '30px'
      borderTop: '1px solid #e7e9ee'
      paddingTop: '10px'

    '.logo-colour':
      color: '#2bde73'

    '.logo-image':
      background: '#2bde73'
      color: '#fff'
      display: 'inline-block'
      fontFamily: '"Source Code Pro", monospace'
      fontWeight: '200'
      padding: '12px 6px 7px 6px'
      marginRight: '12px'

    '.logo-image-dollar':
      display: 'inline-block'
      fontSize: '34px'

    '.logo-image-pipe':
      display: 'inline-block'
      paddingLeft: '2px'
      fontSize: '32px'

    '.logo-text':
      color: '#000'
      display: 'inline-block'
      fontFamily: '"Open Sans", sans-serif'
      fontSize: '30px'
      fontWeight: '300'
      height: '40px'
      letterSpacing: '0.5px'
      paddingTop: '9px'
      verticalAlign: 'top'
      '@media all and (max-width: 600px)':
        fontSize: '20px'
      '@media all and (max-width: 370px)':
        fontSize: '16px'

    '.main':
      display: 'table-row'
      height: '100%'

    '.navicon':
      cursor: 'pointer'
      display: 'none'
      padding: '28px 17px 27px 20px'
      position: 'absolute'
      right: '0px'
      top: '0px'
      '-userSelect': 'none'
      div:
        background: "#{MENU_SVG} no-repeat"
        backgroundSize: '30px 30px'
        width: '30px'
        height: '30px'
      '@media all and (max-width: 922px)':
        display: 'block'

    '.navlinks':
      float: 'right'
      marginTop: '11px'
      a:
        borderRadius: '5px'
        color: '#000'
        fontSize: '16px'
        padding: '7px 12px'
        textDecoration: 'none'
        transition: 'background-color 50ms ease-out, color 50ms ease-out'
        '&:hover':
          background: '#ecf0f1'
        '&:active':
          background: '#ecf0f1'
      '@media all and (max-width: 922px)':
        background: '#fff'
        boxShadow: '-2px 3px 5px 0px rgba(0,0,0,0.19)'
        display: 'none'
        float: 'none'
        position: 'absolute'
        top: '82px'
        right: '0px'
        marginTop: '0px'
        width: '100%'
        zIndex: '500'
        a:
          borderRadius: '0px'
          color: '#232d32'
          display: 'block'
          padding: '20px 12px'
          textAlign: 'right'
          '&:hover':
            background: '#2bde73'
            color: '#fff'
          '&:active':
            background: '#2bde73'
            color: '#fff'

    '.notice':
      padding: '20px 0 40px 0'
      fontSize: '30px'
      lineHeight: '42px'
      '@media all and (max-width: 600px)':
        fontSize: '18px'
        lineHeight: '27px'

    '.notice-sponsors':
      padding: '20px 0 20px 0'
      fontSize: '30px'
      lineHeight: '42px'
      marginBottom: '10px'
      '@media all and (max-width: 600px)':
        padding: '10px 0 10px 0'
        fontSize: '21px'
        lineHeight: '30px'

    '.pad-bottom':
      paddingBottom: '60px'

    '.page':
      padding: '20px 0'
      width: '600px'
      '@media all and (max-width: 922px)':
        width: '100%'

    '.page-header':
      background: '#ecf0f1'
      height: '450px'
      position: 'relative'
      userSelect: 'none'

    '.page-title':
      color: '#232d32'
      fontSize: '80px'
      fontWeight: '700'
      lineHeight: '80px'
      position: 'absolute'
      top: '170px'
      width: '100%'
      '@media all and (max-width: 922px)':
        textAlign: 'center'
      '@media all and (max-width: 600px)':
        fontSize: '50px'
        lineHeight: '60px'
        textAlign: 'center'

    '.page-title-pad':
      margin: '0 auto'
      position: 'relative'
      width: '900px'
      '@media all and (max-width: 922px)':
        padding: '0 15px'
        margin: '0'
        width: '100%'
      '@media all and (max-width: 600px)':
        padding: '0'
        margin: '0'
        width: '100%'

    '.preview-warn':
      background: '#ffc788'
      marginBottom: '20px'
      padding: '10px 5px'
      textAlign: 'center'

    '.project-activity-bar':
      lineHeight: '40px'
      br:
        display: 'none'
        '@media all and (max-width: 600px)':
          display: 'block'

    '.project-title':
      fontSize: '48px'
      fontWeight: '400'
      lineHeight: '64px'
      marginBottom: '20px'
      '@media all and (max-width: 922px)':
        fontSize: '30px'
        lineHeight: '40px'

    '.select-box':
      display: 'inline-block'
      border: '1px solid #ccc'
      borderRadius: '3px'
      overflow: 'hidden'
      position: 'relative'
      '&:after':
        top: '50%'
        right: '13px'
        border: 'solid transparent'
        content: '" "'
        height: '0px'
        width: '0px'
        position: 'absolute'
        pointerEvents: 'none'
        borderColor: 'rgba(0, 0, 0, 0)'
        borderTopColor: '#000000'
        borderWidth: '5px'
        marginTop: '-2px'
        zIndex: '100'
      select:
        padding: '15px 22px 15px 12px'
        width: '130%'
        border: 'none'
        boxShadow: 'none'
        background: 'transparent'
        backgroundImage: 'none'
        '-webkit-appearance': 'none'
        '-moz-appearance': 'none'
        appearance: 'none'
      'select:-moz-focusring':
        color: 'transparent'
        textShadow: '0 0 0 #000'
      'select:focus':
        outline: 'none'

    '.share':
      borderRadius: '5px'
      borderStyle: 'solid'
      borderWidth: '1px'
      color: '#fff'
      display: 'block'
      padding: '10px'
      margin: '15px 0'
      width: '100%'
      position: 'relative'
      transition: 'background-color 400ms ease-out, border-color 400ms ease-out'
      '&:hover':
        border: '1px solid #fff'
      div:
        paddingLeft: '32px'
        lineHeight: '24px'
        width: '100%'
        height: '24px'

    '.share-email':
      background: '#666'
      borderColor: '#666'
      '&:hover':
        background: '#444'
        borderColor: '#444'
      div:
        background: "#{EMAIL_WHITE} no-repeat"

    '.share-facebook':
      background: '#3b5998'
      borderColor: '#3b5998'
      '&:hover':
        background: '#324b80'
        borderColor: '#324b80'
      div:
        background: "#{FACEBOOK_WHITE} no-repeat"

    '.share-twitter':
      background: '#00aced'
      borderColor: '#00aced'
      '&:hover':
        background: '#0093cb'
        borderColor: '#0093cb'
      div:
        background: "#{TWITTER_WHITE} no-repeat"

    '.show-navlinks':
      '.navlinks':
        display: 'block !important'

    '.sponsor-tier':
      padding: '40px 0 30px 20px'
      '@media all and (max-width: 600px)':
        padding: '0px'
      '.sponsor-profile':
        float: 'left'
        height: '210px'
        margin: '0 20px 15px 0'
        overflow: 'hidden'
        textAlign: 'center'
        width: '400px'
        '@media all and (max-width: 600px)':
          float: 'none'
          height: 'auto'
          margin: '30px auto'
          overflow: 'visible'
          padding: '0px'
          width: '90%'
        img:
          height: '120px'
          marginBottom: '10px'
          '@media all and (max-width: 600px)':
            height: '80px'
            marginBottom: '10px'
        '.sponsor-link':
          a:
            borderBottom: "1px dotted #{LINK_COLOUR}"
            color: '#232d32'
            paddingBottom: '4px'
            textDecoration: 'none'
            '&:hover':
              borderBottom: "1px solid transparent"

    '.sponsor-tier-heading':
      background: '#ecf0f1'
      display: 'inline-block'
      padding: '8px 12px'
      fontSize: '18px'

    '.sponsored-by-heading':
      background: '#ecf0f1'
      h3:
        fontSize: '12px'
        lineHeight: '12px'
        padding: '12px 0 10px 0'
        margin: '0'

    '.sponsored-by-profiles':
      '.sponsor-profile':
        float: 'left'
        textAlign: 'center'
        padding: '10px'
        margin: '15px 15px 15px 0'
        width: '320px'
        height: '170px'
        overflow: 'hidden'
        '@media all and (max-width: 700px)':
          width: '100%'
          height: 'auto'
          margin: '15px 0 5px 0'
        img:
          marginBottom: '15px'
          height: '80px'
          '@media all and (max-width: 700px)':
            marginBottom: '10px'
        '.sponsor-link':
          a:
            borderBottom: "1px dotted #{LINK_COLOUR}"
            color: '#232d32'
            paddingBottom: '4px'
            '&:hover':
              borderBottom: "1px solid transparent"

    # '.syntax':
    #   '.c':
    #     color: '#919191' # Comment
    #   '.cm':
    #     color: '#919191' # Comment.Multiline
    #   '.cp':
    #     color: '#919191' # Comment.Preproc
    #   '.cs':
    #     color: '#919191' # Comment.Special
    #   '.c1':
    #     color: '#919191' # Comment.Single
    #   '.err':
    #     color: '#a61717'
    #     backgroundColor: '#e3d2d2' # Error
    #   '.g':
    #     color: '#101010' # Generic
    #   '.gd':
    #     color: '#d22323' # Generic.Deleted
    #   '.ge':
    #     color: '#101010'
    #     fontStyle: 'italic' # Generic.Emph
    #   '.gh':
    #     color: '#101010' # Generic.Heading
    #   '.gi':
    #     color: '#589819' # Generic.Inserted
    #   '.go':
    #     color: '#6a6a6a' # Generic.Output
    #   '.gp':
    #     color: '#bb8844' # Generic.Prompt
    #   '.gr':
    #     color: '#d22323' # Generic.Error
    #   '.gs':
    #     color: '#101010' # Generic.Strong
    #   '.gt':
    #     color: '#d22323' # Generic.Traceback
    #   '.gu':
    #     color: '#101010' # Generic.Subheading
    #   '.k':
    #     # color: '#c32528' # Keyword: (espian red)
    #     color: '#ff5600' # Keyword (orangy)
    #   '.kc':
    #     color: '#ff5600' # Keyword.Constant
    #   '.kd':
    #     color: '#ff5600' # Keyword.Declaration
    #   '.kd':
    #     color: '#ff5600' # Keyword.Declaration
    #   '.kn':
    #     color: '#ff5600' # Keyword
    #   '.kp':
    #     color: '#ff5600' # Keyword.Pseudo
    #   '.kr':
    #     color: '#ff5600' # Keyword.Reserved
    #   '.kt':
    #     color: '#ff5600' # Keyword.Type
    #   '.l':
    #     color: '#101010' # Literal
    #   '.ld':
    #     color: '#101010' # Literal.Date
    #   '.m':
    #     # color: '#3677a9' # Literal.Number (darkish pastely blue)
    #     # color: '#00a33f' # Literal.Number (brightish green)
    #     # color: '#1550a2' # Literal.Number (darker blue)
    #     color: '#5d90cd' # Literal.Number (pastely blue)
    #   '.mf':
    #     color: '#5d90cd' # Literal.Number.Float
    #   '.mh':
    #     color: '#5d90cd' # Literal.Number.Hex
    #   '.mi':
    #     color: '#5d90cd' # Literal.Number.Integer
    #   '.il':
    #     color: '#5d90cd' # Literal.Number.Integer.Long
    #   '.mo':
    #     color: '#5d90cd' # Literal.Number.Oct
    #   '.bp':
    #     color: '#a535ae' # Name.Builtin.Pseudo
    #   '.n':
    #     color: '#101010' # Name
    #   '.na':
    #     color: '#bbbbbb' # Name.Attribute
    #   '.nb':
    #     # color: '#bf78cc' # Name.Builtin (pastely purple)
    #     # color: '#af956f' # Name.Builtin (pastely light brown)
    #     color: '#a535ae' # Name.Builtin (brightish pastely purple)
    #   '.nc':
    #     color: '#101010' # Name.Class
    #   '.nd':
    #     color: '#6d8091' # Name.Decorator
    #   '.ne':
    #     color: '#af956f' # Name.Exception
    #   '.nf':
    #     # color: '#3677a9' # Name.Function
    #     color: '#1550a2' # Name.Function
    #   '.ni':
    #     color: '#101010' # Name.Entity
    #   '.nl':
    #     color: '#101010' # Name.Label
    #   '.nn':
    #     # color: '#101010' # Name.Namespace
    #     color: '#101010' # Name.Namespace
    #   '.no':
    #     color: '#101010' # Name.Constant
    #   '.nx':
    #     color: '#101010' # Name.Other
    #   '.nt':
    #     color: '#6d8091' # Name.Tag
    #   '.nv':
    #     color: '#101010' # Name.Variable
    #   '.vc':
    #     color: '#101010' # Name.Variable.Class
    #   '.vg':
    #     color: '#101010' # Name.Variable.Global
    #   '.vi':
    #     color: '#101010' # Name.Variable.Instance
    #   '.py':
    #     color: '#101010' # Name.Property
    #   '.o':
    #     color: '#ff5600' # Operator */ # orangy
    #   '.o':
    #     color: '#101010' # Operator
    #   '.ow':
    #     color: '#101010' # Operator.Word
    #   '.p':
    #     color: '#101010' # Punctuation
    #   '.s':
    #     # color: '#dd1144' # Literal.String (darkish red)
    #     # color: '#c32528' # Literal.String (espian red)
    #     # color: '#39946a' # Literal.String (pastely greeny)
    #     # color: '#5d90cd' # Literal.String (pastely blue)
    #     color: '#00a33f' # Literal.String (brightish green)
    #   '.sb':
    #     color: '#00a33f' # Literal.String.Backtick
    #   '.sc':
    #     color: '#00a33f' # Literal.String.Char
    #   '.sd':
    #     color: '#767676' # Literal.String.Doc
    #   '.se':
    #     color: '#00a33f' # Literal.String.Escape
    #   '.sh':
    #     color: '#00a33f' # Literal.String.Heredoc
    #   '.si':
    #     color: '#00a33f' # Literal.String.Interpol
    #   '.sr':
    #     color: '#00a33f' # Literal.String.Regex
    #   '.ss':
    #     color: '#00a33f' # Literal.String.Symbol
    #   '.sx':
    #     color: '#00a33f' # Literal.String.Other
    #   '.s1':
    #     color: '#00a33f' # Literal.String.Single
    #   '.s2':
    #     color: '#00a33f' # Literal.String.Double
    #   '.w':
    #     color: '#101010' # Text.Whitespace
    #   '.x':
    #     color: '#101010' # Other

    # '.syntax.bash .nb':
    #   color: '#101010'
    # '.syntax.bash .nv':
    #   color: '#c32528'
    # '.syntax.css .k':
    #   color: '#606060'
    # '.syntax.css .nc':
    #   color: '#c32528'
    # '.syntax.css .nf':
    #   color: '#c32528'
    # '.syntax.css .nt':
    #   color: '#c32528'
    # '.syntax.rst .k':
    #   color: '#5d90cd'
    # '.syntax.rst .ow':
    #   color: '#5d90cd'
    # '.syntax.rst .p':
    #   color: '#5d90cd'
    # '.syntax.yaml .l-Scalar-Plain':
    #   color: '#5d90cd'
    # '.syntax.yaml .p-Indicator':
    #   color: '#101010'

    '.team-profile-follow':
      paddingBottom: '20px'
      paddingTop: '20px'
      a:
        position: 'relative'
        img:
          height: '33px'
          marginTop: '9px'
          marginLeft: '3px'
          position: 'absolute'
        '.team-profile-icon':
          position: 'absolute'
          top: '5px'
          left: '5px'
          width: '30px'
          height: '30px'
        '.team-profile-github':
          background: "#{GITHUB_BLACK} no-repeat"
        '.team-profile-linkedin':
          background: "#{LINKEDIN_ICON} no-repeat"
        '.team-profile-twitter':
          background: "#{TWITTER_ICON} no-repeat"

    '.team-profile-follow-count':
      color: '#a7b2b8'
      display: 'block'
      fontSize: '15px'
      lineHeight: '18px'
      paddingLeft: '52px'

    '.team-profile-follow-username':
      color: '#232d32'
      fontWeight: '700'
      marginLeft: '52px'
      '&:hover':
        borderBottom: '1px dotted #232d32'

    '.team-profile-image':
      paddingTop: '10px'
      paddingBottom: '6px'
      textAlign: 'center'
      img:
        width: '200px'

    '.team-profile-name':
      fontSize: '20px'
      fontWeight: '300'
      paddingTop: '8px'
      paddingBottom: '7px'

    '.toc':
      ul:
        li:
          marginBottom: '5px'
          a:
            fontWeight: '400'

    '.users-list':
      borderCollapse: 'collapse'
      borderSpacing: '0'
      border: '1px solid #ececec'
      margin: '30px 0px 30px 0px'
      width: '100%'
      maxWidth: '100%'
      thead:
        backgroundColor: '#f0f0f0'
        color: '#000'
        textAlign: 'left'
      'th, td':
        borderLeft: '1px solid #ececec'
        borderWidth: '0 0 0 1px'
        margin: '0'
        padding: '20px 20px'
      'td:first-child, th:first-child':
        borderLeftWidth: '0'
      'td.constrained-width':
        width: '350px'
        maxWidth: '350px'
        overflow: 'hidden'
        textOverflow: 'ellipsis'
      span:
        color: 'red'
        position: 'relative'
        top: '-0.5em'
        fontSize: '80%'

    # '*':
    #   background: '#000 !important'
    #   color: '#0f0 !important'
    #   outline: 'solid #f00 1px !important'

  return
