<%namespace name="layout" file="email-layout"/>
<%layout:line>Hi there,</%layout:line>
<%layout:line>There was an error processing your GitFund sponsorship.</%layout:line>
<%layout:line>We'll try charging your card again over the next two weeks. But if you would like to update your payment information to use a different card or to change your support level, please use the authorised link below:</%layout:line>
<%layout:button href="${authlink}">Update Payment Info</%layout:button>
<%layout:line>If you feel there's been a mistake or have any questions, please email us at <%layout:link href="mailto:team@gitfund.io">team@gitfund.io</%layout:link>. Thanks!</%layout:line>