<html xmlns="http://www.w3.org/1999/xhtml">
<head>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
<title>plan report</title>
<style type="text/css">
<!--
/************ Table ************/
.cplantable {border-collapse: collapse;border: 1px solid #ccc;}    
.cplantable thead td {font-size: 14px;color: #333333;text-align: center;background: repeat-x top center;border: 1px solid #ccc; font-weight:bold;}
.cplantable tbody tr {background: #fff;font-size: 12px;color: #666666;}           
.cplantable tbody tr.alt-row {background: #f2f7fc;}               
.cplantable td{line-height:20px;text-align: left;padding:4px 10px 3px 10px;height: 18px;border: 1px solid #ccc;}

textarea {
-moz-box-shadow:0 0 0 #E7E7E7;
-moz-box-sizing:border-box;
border-color:#CCCCCC #999999 #999999 #CCCCCC;
border-style:solid;
border-width:0px;
font-family:arial,sans-serif;
font-size:12px;
height:100px;
margin:0px auto;
outline-color:-moz-use-text-color;
outline-style:none;
outline-width:medium;
padding:0px;
width:300px;
}
-->
</style>
</head>

<body>

<table class="cplantable">
	<tr><td style='white-space:nowrap'>测试目的</td> <td>{planReportTarget}</td> </tr>
	<tr><td>执行详情</td> <td>{planReportDetail}</td> </tr>
	<tr><td>测试总结</td> <td>{planreportSummary}</td> </tr>
	<tr><td>遗留问题</td> <td>{planreportIssues}</td> </tr>
	<tr><td colspan=2 style='background-color: #eeeeee;'><strong>用例执行</strong></td></tr> 
	<tr><td colspan=2>{planReportCaseSummary}</td></tr>
</table>

</body>
</html>
