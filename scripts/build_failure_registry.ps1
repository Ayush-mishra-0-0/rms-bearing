$ErrorActionPreference='Stop'
$inputPath=(Resolve-Path 'docs\1.1 IR Loco Asset Failure Report(Owner).xlsx')
$excel=New-Object -ComObject Excel.Application
$excel.Visible=$false
try {
  $book=$excel.Workbooks.Open($inputPath); $sheet=$book.Worksheets.Item(1); $used=$sheet.UsedRange
  $headers=@{}; for($c=1;$c -le $used.Columns.Count;$c++){ $headers[$sheet.Cells.Item(2,$c).Text.Trim()]=$c }
  function GetCell($row,$name){ $i=$headers[$name]; if($null -eq $i){return ''}; return ($sheet.Cells.Item($row,$i).Text -replace '[\r\n]+',' ').Trim() }
  $all=@()
  for($r=3;$r -le $used.Rows.Count;$r++){
    $id=GetCell $r 'FailureId'; if([string]::IsNullOrWhiteSpace($id)){continue}
    $equipment=GetCell $r 'Equipment'; $defect=GetCell $r 'Failure / Defect'
    $narrative=((GetCell $r 'Line Attention(TLC)')+' '+(GetCell $r 'Shed Investigation Remarks')+' '+(GetCell $r 'ZTLC Remark')+' '+$defect)
    $t=$narrative.ToLowerInvariant()
    $label='REJECT';$confidence='HIGH';$reason='No explicit mechanical traction-motor diagnosis; record describes an electrical, sensor, control, operational, or unconfirmed isolation event.'
    if($t -match 'axle.{0,30}lock|locked.{0,30}axle|bearing.{0,30}seiz|seiz.{0,30}bearing|de bearing|nde bearing|labyrinth.{0,40}(seiz|rub|came out|displaced)|pinion.{0,30}(cut|shaft broken|parted)|wheel.{0,30}not rotating|rotor.{0,30}(jam|stuck).{0,30}(mechan|bearing)|gear.{0,30}oil.{0,80}(bearing|seiz|jam)'){
      $label='LEVEL_1';$confidence='HIGH';$reason='Maintenance narrative explicitly identifies axle/bearing/labyrinth/pinion seizure, lock, or mechanical jamming.'
    } elseif($t -match 'smoke.{0,80}(tm|traction motor|wheel|gear)|wheel.{0,30}heating|rotor.{0,40}(damag|rub|stuck)|stator.{0,40}(burst|damag)|winding.{0,40}(burst|burn|flash)|burnt.{0,40}(tm|motor)|gear.?case.{0,40}(damage|leak)|abnormal.{0,30}vibration|torque arm bolt|teeth.{0,40}(scored|pitmark|grooved)'){
      $label='LEVEL_2';$confidence='HIGH';$reason='Maintenance narrative identifies a serious mechanical traction-motor, rotor/stator, gearcase, wheel-heating, smoke, or vibration failure.'
    } elseif($t -match 'loco not arrived|cause.*(not established|will be established)|exact cause'){
      $confidence='LOW';$reason='No confirmed diagnosis is recorded; isolation alone is not a mechanical positive label.'
    }
    $summary=($defect+'; '+$narrative); if($summary.Length -gt 500){$summary=$summary.Substring(0,500)}
    $all += [pscustomobject][ordered]@{FailureID=$id;Loco=(GetCell $r 'Loco No.');Date=(GetCell $r 'Date of Failure');Equipment=$equipment;FailureDescription=$defect;AssignedLabel=$label;Confidence=$confidence;Reason=$reason;FailureSummary=$summary}
  }
  $all | Export-Csv -NoTypeInformation -Encoding utf8 'data\processed\owner_failure_classification.csv'
  $all | Where-Object {$_.AssignedLabel -in 'LEVEL_1','LEVEL_2'} | Select-Object FailureID,Loco,Date,Equipment,@{Name='Label';Expression={$_.AssignedLabel}},Confidence,FailureSummary | Export-Csv -NoTypeInformation -Encoding utf8 'data\processed\ground_truth_failure_registry.csv'
  $all | Group-Object AssignedLabel | Select-Object Name,Count | Format-Table -AutoSize
  Write-Output "TOTAL=$($all.Count) POSITIVES=$(($all|Where-Object {$_.AssignedLabel -ne 'REJECT'}).Count)"
  $all | Where-Object {$_.AssignedLabel -ne 'REJECT'} | Select-Object FailureID,Loco,Date,FailureDescription,AssignedLabel,Confidence | Format-Table -Wrap -AutoSize
  $book.Close($false)
} finally { $excel.Quit(); [void][Runtime.InteropServices.Marshal]::ReleaseComObject($excel) }
